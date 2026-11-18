import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {plan,gateContact,redactResult} from "./core.ts";
const TOKEN_SHA256="48a231313669e9fbe71ced2be12d66e87a8f5139abba650cbc76f80583649788"; // existing private Vault token, never printed
function json(body:unknown,status=200){return new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});}
async function hash(s:string){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("");}
function safeEq(a:string,b:string){if(a.length!==b.length)return false;let n=0;for(let i=0;i<a.length;i++)n|=a.charCodeAt(i)^b.charCodeAt(i);return n===0;}
Deno.serve(async(req:Request)=>{
 if(req.method!=="POST")return json({state:"METHOD_NOT_ALLOWED"},405);
 const token=req.headers.get("x-news001-lab-token")||"";
 if(token.length!==64||!safeEq(await hash(token),TOKEN_SHA256))return json({state:"UNAUTHORIZED"},401);
 let body:Record<string,unknown>;try{body=await req.json();if(!body||Array.isArray(body)||typeof body!=="object")throw Error("BAD_JSON");}catch{return json({state:"BAD_JSON"},400);}
 if(body.action!=="sync"&&body.action!=="probe")return json({state:"UNSUPPORTED_ACTION"},400);
 const key=Deno.env.get("BREVO_API_KEY")||"";if(!key)return json({state:"BREVO_SECRET_MISSING"},503);
 const remote=async(path:string,method:"GET"|"POST"|"PUT"="GET",payload?:unknown)=>{
   if(!(/^(\/contacts\/[^/]+|\/contacts)$/.test(path))||!["GET","POST","PUT"].includes(method))throw Error("PATH_DENIED");
   const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),9000);
   try {
      const r=await fetch("https://api.brevo.com/v3"+path,{method,headers:{"api-key":key,"accept":"application/json","content-type":"application/json"},redirect:"error",signal:ctrl.signal,...(payload?{body:JSON.stringify(payload)}:{})});
      if(r.status===404&&method==="GET")return {notFound:true};
      if(!r.ok)throw Error("BREVO_HTTP_"+r.status);
      if(r.status===204)return {};
      const txt=await r.text();if(txt.length>200000)throw Error("RESPONSE_TOO_BIG");
      return txt?JSON.parse(txt):{};
   }finally{clearTimeout(timer);}
 };
 if(body.action==="probe"){
   if(body.test_email!=="carlosj.munozcabeza@gmail.com")return json({state:"PROBE_DENIED"},403);
   try{const data=await remote("/contacts/"+encodeURIComponent(body.test_email as string));return json({state:"OWNER_CONTACT_PROBED",contact_found:!data.notFound,email_blacklisted:data.emailBlacklisted,list_ids:data.listIds||[],unsubscribed_lists:data.listUnsubscribed||[],mutations:0});}
   catch(e){return json({state:"PROBE_FAILED",error:String(e).slice(0,90)},503);}
 }
 const p=plan(body);if(p.state!=="ELIGIBLE")return json(redactResult(p),422);
 const release=body.release_approved==="NEWS001_OWNER_SINGLE_OPTIN_20261118";
 if(!release)return json({state:"DRY_RUN_ELIGIBLE",list_id:p.list_id,brevo_calls:0,mutations:0});
 const u="/contacts/"+encodeURIComponent(p.email);
 try{
   const prior=await remote(u);
   if(!prior.notFound){
     const gate=gateContact(prior,p.list_id);
     if(gate.state==="HOLD")return json({state:"HOLD",reason:gate.reason,list_id:p.list_id,mutations:0},409);
     if(gate.state==="ALREADY_SUBSCRIBED")return json({state:"ALREADY_SUBSCRIBED",list_id:p.list_id,mutations:0});
     await remote(u,"PUT",{listIds:[p.list_id]});
   }else await remote("/contacts","POST",{email:p.email,listIds:[p.list_id],updateEnabled:false});
   const check=await remote(u);
   if(check.notFound||gateContact(check,p.list_id).state!=="ALREADY_SUBSCRIBED")return json({state:"POST_WRITE_VERIFICATION_HOLD",mutations:1},409);
   return json({state:"CONTACT_SYNC_VERIFIED",list_id:p.list_id,welcome_by_existing_brevo_automation:true,commercial_campaign_send:false,mutations:1});
 }catch(e){return json({state:"BREVO_CONTACT_SYNC_HOLD",code:String(e).replace(/.*BREVO_HTTP_/,"BREVO_HTTP_").slice(0,90),no_campaign_sent:true},422);}
});
