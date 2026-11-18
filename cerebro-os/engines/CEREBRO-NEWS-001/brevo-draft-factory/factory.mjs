import {readFileSync} from "node:fs";
import {join} from "node:path";
import {createHash} from "node:crypto";
export const TARGETS=Object.freeze({b2b:18,b2c:17});
export function validate(kind,html,report){
  if(!Object.hasOwn(TARGETS,kind))throw Error("BAD_AUDIENCE");
  if(report?.engine_id!=="CEREBRO-NEWS-001"||report.environment!=="LAB"||
     report.send_enabled!==false||report.publish_enabled!==false||
     report.approved!==false||report.api_called!==false)throw Error("NOT_SAFE_LAB_REPORT");
  const r=report.audiences?.[kind];
  if(r?.brevo?.status!=="LAB_PASS")throw Error("EDITORIAL_QA_NOT_PASS");
  if(r.brevo.html_sha256!==createHash("sha256").update(html).digest("hex"))throw Error("HASH_MISMATCH");
  const blocks=[...html.matchAll(/\bdata-block=["']([^"']+)["']/gi)].map(x=>x[1]);
  if(blocks.length!==10||new Set(blocks).size!==10)throw Error("MISSING_10_MODULES");
  if((html.match(/<a[\s>]/gi)||[]).length!==13)throw Error("MISSING_13_LINKS");
  const imgs=[...html.matchAll(/<img\b[^>]*>/gi)];
  if(imgs.length!==2||imgs.some(m=>!m[0].includes("https://fenixcapital.es/wp-content/uploads/")))throw Error("MISSING_PUBLIC_BRAND_ASSETS");
  if(!html.includes("{{ unsubscribe }}"))throw Error("UNSUBSCRIBE_MISSING");
  if(/data:image|<script|javascript:|#870064/i.test(html))throw Error("REJECT_BAD_HTML");
  if(!r.subject||!r.preheader)throw Error("COPY_MISSING");
  if(Buffer.byteLength(html)>950000)throw Error("HTML_TOO_LARGE");
  return {listId:TARGETS[kind],subject:r.subject,preheader:r.preheader};
}
export function build(kind,html,report){
  const v=validate(kind,html,report);
  if(!/^\d{4}w\d{2}$/.test(report.weekly_campaign_suffix||""))throw Error("BAD_WEEK");
  return {name:"NEWS001-"+kind.toUpperCase()+"-"+report.weekly_campaign_suffix+"-CEREBRO-ORIGINAL-10",
    sender:{name:"Fénix Capital",email:"hipotecas@fenixcapital.es"},
    recipients:{listIds:[v.listId]},subject:v.subject,previewText:v.preheader,
    htmlContent:html,mirrorActive:true,replyTo:"hipotecas@fenixcapital.es",tag:"NEWS001_LAB_DRAFT"};
}
export async function prepare({dir,fetcher=fetch,key=process.env.BREVO_API_KEY||"",enable=process.env.NEWS001_CREATE_DRAFTS==="true"}){
  if(!enable)return {state:"DISABLED_DEFAULT",sent:false,apiCalled:false};
  if(!key)throw Error("NO_BREVO_API_KEY");
  const report=JSON.parse(readFileSync(join(dir,"RESULTADO_PRUEBA.json"),"utf8"));
  const payloads={};
  for(const kind of ["b2b","b2c"])
   payloads[kind]=build(kind,readFileSync(join(dir,"NEWS_FENIX_"+kind+"_BREVO_BORRADOR.html"),"utf8"),report);
  async function api(path,method="GET",data=null){
    if(!/^\/emailCampaigns(?:\?type=classic&status=draft&limit=100&offset=0)?$/.test(path)||
      !["GET","POST"].includes(method))throw Error("NOT_ALLOWLISTED");
    const response=await fetcher("https://api.brevo.com/v3"+path,{method,
      headers:{"api-key":key,"accept":"application/json","content-type":"application/json"},
      ...(data?{body:JSON.stringify(data)}:{})});
    if(!response.ok)throw Error("BREVO_HTTP_"+response.status);
    return response.json();
  }
  const existing=await api("/emailCampaigns?type=classic&status=draft&limit=100&offset=0");
  if(!Array.isArray(existing.campaigns))throw Error("LIST_DRAFTS_MISSING");
  const results=[];
  for(const kind of ["b2b","b2c"]){
    const payload=payloads[kind];
    const old=existing.campaigns.find(c=>c.name===payload.name);
    if(old){results.push({kind,state:"EXISTING_DRAFT",id:old.id});continue;}
    const created=await api("/emailCampaigns","POST",payload);
    if(!Number.isInteger(created.id)||created.id<1)throw Error("CREATE_DRAFT_INVALID");
    results.push({kind,state:"NEW_DRAFT_NOT_SENT",id:created.id});
  }
  return {state:"TWO_DRAFTS_READY",results,sent:false,changedOldAutomations:false};
}
