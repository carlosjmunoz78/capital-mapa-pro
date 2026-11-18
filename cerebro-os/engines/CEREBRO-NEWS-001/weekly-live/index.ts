import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {render,headline} from "./engine.ts";
const DIGEST="48a231313669e9fbe71ced2be12d66e87a8f5139abba650cbc76f80583649788";
const OWNER="carlosj.munozcabeza@gmail.com";
const reply=(x:unknown,status=200)=>new Response(JSON.stringify(x),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});
async function sha(s:string){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));return [...new Uint8Array(b)].map(v=>v.toString(16).padStart(2,"0")).join("");}
function equal(a:string,b:string){if(a.length!==b.length)return false;let x=0;for(let i=0;i<a.length;i++)x|=a.charCodeAt(i)^b.charCodeAt(i);return x===0;}
async function brevo(path:string,key:string,method="GET",data?:unknown){
 if(!/^\/(emailCampaigns(?:\/[0-9]+(?:\/sendTest)?)?(?:\?limit=\d+&offset=\d+)?|contacts\/lists\/(17|18))$/.test(path)||!["GET","POST"].includes(method))throw Error("API_DENIED");
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),10000);
 try{const r=await fetch("https://api.brevo.com/v3"+path,{method,headers:{"api-key":key,"accept":"application/json","content-type":"application/json"},redirect:"error",signal:ctrl.signal,...(data?{body:JSON.stringify(data)}:{})});
 const txt=await r.text();if(txt.length>700000)throw Error("API_OVERSIZE");
 if(!r.ok)throw Error("BREVO_HTTP_"+r.status);
 return txt?JSON.parse(txt):{};}finally{clearTimeout(timer);}
}
async function audiences(key:string){
 const v=await Promise.all([17,18].map(id=>brevo("/contacts/lists/"+id,key)));
 const n=v.map((x,i)=>({list_id:[17,18][i],subscribers:Number(x.totalSubscribers)}));
 if(n.some(x=>!Number.isFinite(x.subscribers)||x.subscribers<1||x.subscribers>140)||n.reduce((p,x)=>p+x.subscribers,0)>280)throw Error("HOLD_DAILY_QUOTA");
 return n;
}
async function newCampaign(key:string,p:any,scheduledAt?:string){
 return await brevo("/emailCampaigns",key,"POST",{name:p.name,sender:{name:"Fénix Capital",email:"hipotecas@fenixcapital.es"},replyTo:"hipotecas@fenixcapital.es",subject:p.subject,previewText:p.previewText,recipients:{listIds:[p.listId]},htmlContent:p.htmlContent,...(scheduledAt?{scheduledAt}:{})});
}
Deno.serve(async(req:Request)=>{
 if(req.method!=="POST")return reply({state:"METHOD_NOT_ALLOWED"},405);
 const token=req.headers.get("x-news001-lab-token")||"";
 if(token.length!==64||!equal(await sha(token),DIGEST))return reply({state:"UNAUTHORIZED"},401);
 let b:any;try{b=await req.json();}catch{return reply({state:"BAD_JSON"},400);}
 if(b?.company_id!=="fenix"||!["preview","draft","owner-test","weekly","pilot-release"].includes(b.action))return reply({state:"ACTION_DENIED"},403);
 const now=new Date();
 try{
 const news=await headline(fetch,now),items=["pro","hogar"].map(a=>render(a,now,news));
 const info=items.map(x=>({audience:x.audience,week:x.week,subject:x.subject,name:x.name,list_id:x.listId,html_chars:x.htmlContent.length,blocks:x.blocks,images:x.images,source:x.source}));
 if(b.action==="preview")return reply({state:"PREVIEW_READY",company_id:"fenix",engine_id:"CEREBRO-NEWS-001",editions:info,commercial_sending:false});
 const key=Deno.env.get("BREVO_API_KEY")||"";if(!key)throw Error("NO_BREVO_KEY");
 const quota=await audiences(key),d=await brevo("/emailCampaigns?limit=50&offset=0",key);
 const current=Array.isArray(d.campaigns)?d.campaigns:[];
 if(b.action==="draft"){
  const created=[];
  for(const x of items){
   const name="NEWS001 PILOT OWNER "+x.audience.toUpperCase()+" "+x.week;
   const before=current.find((y:any)=>y.name===name);
   if(before){created.push({audience:x.audience,id:before.id,state:"EXISTING"});continue;}
   const r=await newCampaign(key,{...x,name});
   created.push({audience:x.audience,id:r.id,state:"CREATED_DRAFT"});
  }
  return reply({state:"PILOT_DRAFTS_CREATED",created,quota,editions:info,commercial_sending:false});
 }
 if(b.action==="owner-test"){
  const sent=[];
  for(const x of items){
   const name="NEWS001 PILOT OWNER "+x.audience.toUpperCase()+" "+x.week;
   const c=current.find((y:any)=>y.name===name);
   if(!Number.isInteger(c?.id))throw Error("PILOT_DRAFT_MISSING");
   const remote=await brevo("/emailCampaigns/"+c.id,key);
   const lists=remote.recipients?.lists||remote.recipients?.listIds||[];
   if(remote.status!=="draft"||lists.length!==1||lists[0]!==x.listId||remote.subject!==x.subject)throw Error("PILOT_NOT_SAFE");
   await brevo("/emailCampaigns/"+c.id+"/sendTest",key,"POST",{emailTo:[OWNER]});
   sent.push({audience:x.audience,campaign_id:c.id,to:"OWNER_ONLY"});
  }
  return reply({state:"OWNER_TESTS_ACCEPTED",sent});
 }
 const pilot=b.action==="pilot-release";
 if(pilot){
  if(now.toISOString().slice(0,10)!=="2026-11-18"||b.pilot_date!=="2026-11-19"||b.owner_tests_verified!==true)throw Error("PILOT_RELEASE_GATE");
 }else if(now.getUTCDay()!==2||now.getUTCHours()<7||now.getUTCHours()>10)throw Error("WEEKLY_WINDOW_GATE");
 const day=pilot?"2026-11-19":now.toISOString().slice(0,10),created=[];
 for(const x of items){
  const old=current.find((y:any)=>y.name===x.name);
  if(old){created.push({audience:x.audience,id:old.id,state:"ALREADY_EXISTS",status:old.status});continue;}
  const at=day+(x.audience==="pro"?"T10:30:00.000Z":"T10:50:00.000Z");
  if(Date.parse(at)-now.getTime()<40*60000||Date.parse(at)-now.getTime()>48*3600000)throw Error("SCHEDULE_WINDOW_GATE");
  const n=await newCampaign(key,x,at);
  if(!Number.isInteger(n.id))throw Error("CAMPAIGN_ID_INVALID");
  const v=await brevo("/emailCampaigns/"+n.id,key);
  created.push({audience:x.audience,id:n.id,status:v.status,scheduled_at:v.scheduledAt||null});
  if(String(v.status).toLowerCase()!=="scheduled")return reply({state:"HOLD_SCHEDULE_NOT_VERIFIED",created},409);
 }
 return reply({state:"TWO_EDITION_WEEKLY_SCHEDULED",created,quota,editions:info,chatgpt_required:false});
 }catch(e){return reply({state:"HOLD",reason:String(e instanceof Error?e.message:e).slice(0,140),commercial_sending:false},422);}
});
