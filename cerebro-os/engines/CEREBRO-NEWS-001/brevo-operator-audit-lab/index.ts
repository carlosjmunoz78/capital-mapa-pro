import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {TARGET_IDS,summarizeCampaign,summarizeTemplate,summarizeTemplates,auditDecision} from "./core.mjs";
import {TARGETS,prepare,verify} from "./repair.mjs";
const TOKEN_SHA256="48a231313669e9fbe71ced2be12d66e87a8f5139abba650cbc76f80583649788";
function out(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});}
async function sha256(v:string){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(v));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("");}
function eq(a:string,b:string){if(a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a.charCodeAt(i)^b.charCodeAt(i);return d===0;}
Deno.serve(async (req:Request)=>{
 if(req.method!=="POST")return out({state:"METHOD_NOT_ALLOWED"},405);
 const u=new URL(req.url);
 const mode=u.pathname.endsWith("/audit")?"audit":u.pathname.endsWith("/export")?"export":u.pathname.endsWith("/repair")?"repair":null;
 if(!mode)return out({state:"NOT_FOUND"},404);
 const token=req.headers.get("x-news001-lab-token")||"";
 if(token.length!==64||!eq(await sha256(token),TOKEN_SHA256))return out({state:"UNAUTHORIZED"},401);
 let body:unknown;try{body=await req.json();}catch{return out({state:"INVALID_JSON"},400);}
 if(!body||typeof body!=="object"||Array.isArray(body)||(body as Record<string,unknown>).action!==mode)return out({state:"BAD_ACTION"},400);
 const key=Deno.env.get("BREVO_API_KEY")||"";
 if(!key)return out({state:"BREVO_SECRET_NOT_CONFIGURED",no_send:true},503);
 const allowed=new Set(["/emailCampaigns/112","/emailCampaigns/113","/smtp/templates/115","/smtp/templates/114","/smtp/templates?limit=50&offset=0"]);
 const read=async(path:string)=>{
  if(!allowed.has(path))throw Error("DENIED_PATH");
  const controller=new AbortController(),tm=setTimeout(()=>controller.abort(),9000);
  try{
   const res=await fetch("https://api.brevo.com/v3"+path,{
    method:"GET",headers:{"api-key":key,"accept":"application/json"},signal:controller.signal,redirect:"error"});
   if(!res.ok)throw Error("BREVO_"+res.status);
   const raw=await res.text();if(raw.length>1500000)throw Error("RESPONSE_OVERSIZE");
   return JSON.parse(raw);
  }finally{clearTimeout(tm);}
 };
 if(mode==="repair"){
  const reqBody=body as Record<string,unknown>;
  if(reqBody.backup_commit!=="931afd65dfe3ff36087d72e15a1134d01d27260b")return out({state:"BACKUP_NOT_CONFIRMED"},409);
  const target=reqBody.target;
  if(typeof target!=="string"||!Object.prototype.hasOwnProperty.call(TARGETS,target))return out({state:"TARGET_DENIED"},403);
  const t=TARGETS[target];
  try {
   const current=await read(t.path);
   const plan=prepare(target,current);
   if(plan.already_done)return out({state:"ALREADY_MATCHES_CANONICAL",target,commercial_sending_authorized:false});
   if(!new Set(["/emailCampaigns/112","/emailCampaigns/113","/smtp/templates/114","/smtp/templates/115"]).has(t.path))
      return out({state:"PUT_PATH_DENIED"},403);
   const ctrl=new AbortController(),tm=setTimeout(()=>ctrl.abort(),10000);
   let status=0;
   try {
    const rs=await fetch("https://api.brevo.com/v3"+plan.path,{
      method:"PUT",headers:{"api-key":key,"accept":"application/json","content-type":"application/json"},
      body:JSON.stringify(plan.payload),redirect:"error",signal:ctrl.signal});
    status=rs.status;
    if(!rs.ok)return out({state:"BREVO_UPDATE_REJECTED",target,status,send_executed:false},422);
   } finally {clearTimeout(tm);}
   const remote=await read(t.path);
   const test=verify(target,remote);
   if(!test.verified_full_length||!test.sufficient_links||test.image_count!==2||
      !test.unsub_token||!test.campaign_still_draft||!test.template_still_inactive)
      return out({state:"POST_UPDATE_QA_FAILED",target,status,test,send_executed:false},409);
   return out({state:"CANONICAL_CONTENT_SAVED",target,status,test,backup_commit:reqBody.backup_commit,
     commercial_sending_authorized:false,send_executed:false,cost_additional_eur:0});
  }catch(e){
   const error=e instanceof Error?e.message:"UNKNOWN";
   return out({state:"REPAIR_HOLD",target,error_code:/^(BAD_|OLD_|SOURCE_|TEMPLATE_|CAMPAIGN_|CANONICAL_|SEND_|BREVO_\d{3}|DENIED_)/.test(error)?error:"UPSTREAM_ERROR",
     send_executed:false,old_workflows_changed:false},422);
  }
 }
 if(mode==="export"){
  // Explicit internal-only backup of four approved editorial assets; no contacts or audience data.
  const requests=[
   ["campaign_b2c_112","/emailCampaigns/112"],
   ["campaign_b2b_113","/emailCampaigns/113"],
   ["template_b2b_114","/smtp/templates/114"],
   ["template_b2c_115","/smtp/templates/115"]
  ] as const;
  const backups:Record<string,unknown>={};
  for(const [name,path] of requests){
   try{
    const x=await read(path);
    if(typeof x?.htmlContent!=="string"||x.htmlContent.length>900000)throw Error("BAD_HTML");
    backups[name]={id:x.id,name:String(x.name||x.templateName||"").slice(0,180),
      subject:String(x.subject||"").slice(0,240),isActive:x.isActive===true,
      status:String(x.status||x.campaignStatus||""),
      htmlContent:x.htmlContent};
   }catch(e){backups[name]={state:"EXPORT_FAILED",code:e instanceof Error&&/^BREVO_\d{3}$/.test(e.message)?e.message:"ERROR"};}
  }
  return out({state:"NEWS001_PRIVATE_MARKETING_HTML_BACKUP",environment:"LAB",
   includes_customer_personal_data:false,never_send:true,backups});
 }
 const targets=[
  ["campaign_b2c","/emailCampaigns/112", (x:unknown)=>summarizeCampaign(x,112)],
  ["campaign_b2b","/emailCampaigns/113", (x:unknown)=>summarizeCampaign(x,113)],
  ["template_b2c","/smtp/templates/115",(x:unknown)=>summarizeTemplate(x,115)],
  ["template_b2b","/smtp/templates/114",(x:unknown)=>summarizeTemplate(x,114)],
  ["templates","/smtp/templates?limit=50&offset=0",(x:unknown)=>summarizeTemplates(x)]
 ] as const;
 const result:Record<string,unknown>={};
 for(const [name,path,parse] of targets){
   try {result[name]=parse(await read(path));}
   catch(e){result[name]={state:"AUDIT_FAILED",code:(e instanceof Error&&/^BREVO_\d{3}$/.test(e.message))?e.message:"UPSTREAM_OR_PARSING_FAILURE"};}
 }
 return out({state:"READ_ONLY_BREVO_AUDIT",environment:"LAB",company_id:"fenix",engine_id:"CEREBRO-NEWS-001",
  target_ids:TARGET_IDS,results:result,gates:auditDecision(result),contact_data_returned:false,commercial_sending_authorized:false,
  mutations:0,cost_additional_eur:0});
});