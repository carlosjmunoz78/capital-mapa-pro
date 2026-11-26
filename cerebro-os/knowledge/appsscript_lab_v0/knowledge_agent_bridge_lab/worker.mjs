import { runCompanySelector } from "./selector.mjs";
import {verifyUmsOidc} from "./ums-oidc.mjs";
import {evaluateIdentityRights} from "./rights-gate.mjs";

const GRANT = Object.freeze({"company_id":"fenix-capital","department_id":"facebook","engine_id":"SOC-FB-FINANCIAL-REAL-ESTATE-V1","agent_id":"FB-00","subagent_id":"FB-00.SA-001","environment":"LAB","version":"2026-11-18.v1"});
const UMS=Object.freeze({"company_id":"fenix","department_id":"ums","engine_id":"FACT-OIDC-LAB-E2E-001","agent_id":"FACT-OIDC-LAB-E2E-001","subagent_id":"FACT-OIDC-LAB-E2E-001","environment":"LAB","version":"0.1.0"});
const QUEUE = "cerebro-facebook-w24-read-canary-lab-eu";
const SOURCES = "KNOWLEDGE-GOOGLE-SHEETS-LAB-001";
const encoder = new TextEncoder();
const allowed = new Set(["RUN","NEGATIVES","VERIFY"]);
const idPattern = /^fb-[a-z0-9-]{8,48}$/;
function base64url(bytes) {
  return btoa(String.fromCharCode(...bytes)).replace(/=/g,"").replace(/\+/g,"-").replace(/\//g,"_");
}
function bytesFromBase64(value) {
  return Uint8Array.from(atob(value), c=>c.charCodeAt(0));
}
async function digest(value) {
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(value))),
    b=>b.toString(16).padStart(2,"0")).join("");
}

function ledger(env,principal=GRANT) {
  return env.AUDIT.jurisdiction("eu").getByName("knowledge-read:"+principal.subagent_id.toLowerCase()+":v1");
}
async function append(env, id, sha, denial=null, principal=GRANT) {
  const result=await ledger(env,principal).append({
    request_id:id, consumer_id:principal.subagent_id, company_id:principal.company_id, engine_id:principal.engine_id,
    version:principal.version, source_id:SOURCES, sha256:sha,
    result:denial ? "DENIED" : "ALLOWED", denial, environment:"LAB",
  });
  if (!["INSERTED","EXISTING"].includes(result.status)) throw Error("AUDIT_REQUIRED");
  return result;
}

async function previewSession(env) {
  const url=new URL(env.GATEWAY_URL);
  if (url.protocol!=="https:" || !url.hostname.endsWith(".vercel.app") ||
      url.pathname!=="/api/knowledge-agents" || url.search || url.hash || !env.PREVIEW_SHARE) throw Error("PREVIEW_CONFIG_INVALID");
  const login=new URL(url);
  login.searchParams.set("_vercel_share",env.PREVIEW_SHARE);
  const response=await fetch(login,{redirect:"manual"});
  const cookies=(response.headers.get("set-cookie")??"").split(/,(?=\s*[^;,]+=)/)
    .map(part=>part.trim().split(";")[0]).filter(part=>part.startsWith("_vercel_"));
  if(!cookies.length && !response.ok) {
    const redirect=response.headers.get("location");
    if(redirect && new URL(redirect,url).hostname!==url.hostname) throw Error("PREVIEW_SHARE_DENIED");
  }
  return {url,cookie:cookies.join("; ")};
}

async function client(env,principal=GRANT) {
  const session=await previewSession(env);
  const key=await crypto.subtle.importKey("pkcs8",bytesFromBase64(principal===UMS?env.UMS_MACHINE_KEY:env.FB_MACHINE_KEY),"Ed25519",false,["sign"]);
  return async (phase, requestId, scope, sha256=null, corruptSignature=false)=>{
    const signed=base64url(encoder.encode(JSON.stringify({
      issuer:principal===UMS?"ums-github-oidc-lab-v1":"fb-shadow-private-lab-v1",subject:principal.subagent_id,audience:session.url.host,
      phase,request_id:requestId,iat:Math.floor(Date.now()/1000),scope,sha256
    })));
    const signature=base64url(new Uint8Array(await crypto.subtle.sign("Ed25519",key,encoder.encode(signed))));
    const body=JSON.stringify({payload:signed,signature:corruptSignature?"A".repeat(86):signature});
    const headers={"content-type":"application/json"};
    if(session.cookie) headers.cookie=session.cookie;
    else session.url.searchParams.set("_vercel_share",env.PREVIEW_SHARE);
    const response=await fetch(session.url,{method:"POST",headers,body,redirect:"manual"});
    if(!response.headers.get("content-type")?.includes("application/json")) throw Error("PREVIEW_MACHINE_HTTP_"+response.status);
    const result=await response.json();
    return {http:response.status,...result};
  };
}

async function execute(env,id) {
  if(env.FB_READ_ENABLED!=="true") {
    await append(env,id+":disabled",null,"CAPABILITY_DISABLED");
    return {result:"CAPABILITY_DISABLED",request_id:id};
  }
  const gateway=await client(env);
  const prepare=await gateway("prepare",id,GRANT);
  if(prepare.http!==200 || !/^[a-f0-9]{64}$/.test(prepare.sha256)) throw Error("KNOWLEDGE_PREPARE_DENIED_"+prepare.http);
  const authorization=await append(env,id+":read",prepare.sha256);
  const read=await gateway("read",id,GRANT,prepare.sha256);
  if(read.http!==200 || read.sha256!==prepare.sha256 ||
      await digest(JSON.stringify(read.bundle))!==prepare.sha256) throw Error("KNOWLEDGE_HASH_REJECTED");
  const bundle=read.bundle;
  const instruction=bundle.items.find(item=>item.knowledge_id==="RULE:K-SCOPE")?.payload;
  const geography=bundle.items.find(item=>item.knowledge_id==="RULE:K-TERRITORY")?.payload;
  if(!instruction?.procedure || !geography?.procedure) throw Error("KNOWLEDGE_RULES_REQUIRED");
  const context={company_id:bundle.company_id,environment:bundle.environment,active:true,verified:true,
    assets:[{company_id:bundle.company_id,asset_id:"fenix-page",active:true}]};
  const trust={company_id:bundle.company_id,environment:bundle.environment,attested:true,
    trust_source:"AUTHENTICATED_KNOWLEDGE_READ",permissions:["READ_CONTEXT"],asset_scopes:["fenix-page"]};
  const request={...GRANT,asset_id:"fenix-page",action:"READ_CONTEXT",
    territory:{country:"España",province:"Córdoba",municipality:"Lucena",zone:"Centro"},
    market_data:{granularity:"province",asserts_zone_fact:true}};
  const decision=runCompanySelector({gateway:trust,registry:context,request},read);
  if(decision.state!=="BLOCK_GEOGRAPHIC_INFERENCE"||decision.external_actions!==0||
    decision.may_publish!==false||decision.may_spend!==false) throw Error("SHADOW_DECISION_UNEXPECTED");
  const decisionHash=await digest(JSON.stringify({decision:decision.state,rules:[instruction,geography]}));
  const receipt=await append(env,id+":decision",decisionHash);
  const persisted=await ledger(env).read(id+":decision");
  if(persisted.records.length!==1 || persisted.records[0].recorded_at!==receipt.recorded_at) throw Error("AUDIT_VERIFY_FAILED");
  return {result:"AGENT_CONSUMED_KNOWLEDGE",request_id:id,consumer_id:GRANT.subagent_id,
    knowledge_sha256:read.sha256,decision:decision.state,decision_sha256:decisionHash,
    audit_read:authorization.status,audit_decision:receipt.status,audit_recorded_at:receipt.recorded_at,
    external_actions:0,certified:0};
}

async function negatives(env,id) {
  const gateway=await client(env);
  const valid=await gateway("prepare",id,GRANT);
  if(valid.http!==200) throw Error("NEGATIVE_PRECONDITION_FAILED");
  const cases=[
    ["identity","prepare",GRANT,null,true,401,"IDENTITY_DENIED"],
    ["company","prepare",{...GRANT,company_id:"fenix"},null,false,403,"COMPANY_DENIED"],
    ["version","prepare",{...GRANT,version:"0.0.0"},null,false,403,"VERSION_DENIED"],
    ["permission","prepare",{...GRANT,subagent_id:"FB-00.SA-002"},null,false,403,"IDENTITY_DENIED"],
    ["hash","read",GRANT,"0".repeat(64),false,409,"INTEGRITY_DENIED"],
  ];
  const out=[];
  for(const [name,phase,scope,sha,fake,http,reason] of cases){
    const r=await gateway(phase,id+"-"+name,scope,sha,fake);
    if(r.http!==http||r.bundle) throw Error("NEGATIVE_FAILED_"+name+"_"+r.http);
    await append(env,id+":"+name,null,reason);
    out.push([name,r.http]);
  }
  return {result:"AGENT_NEGATIVES_PASS",request_id:id,checks:out};
}
async function runUms(request,env){
  if(env.UMS_READ_ENABLED!=="true") return Response.json({status:"CAPABILITY_DISABLED"},{status:503});
  let caller;
  try {caller=await verifyUmsOidc(request.headers.get("authorization"));}
  catch(error) {
    if(request.headers.has("authorization")) {
      const reason=String(error?.message??"");
      console.log(JSON.stringify({status:"UMS_IDENTITY_DENIED",reason:/^OIDC_[A-Z0-9_]{1,35}$/.test(reason)?reason:"OIDC_RUNTIME"}));
    }
    return Response.json({status:"IDENTITY_DENIED"},{status:401});
  }
  const id=caller.request_id;
  try {
    const gateway=await client(env,UMS);
    const prepared=await gateway("prepare",id,UMS);
    if(prepared.http===409&&prepared.status==="DELIVERY_RECEIPT_PENDING"){
      const event={status:"UMS_OIDC_VERIFIED_RECEIPT_PENDING",request_id:id,consumer_id:UMS.subagent_id,commit:caller.commit};
      console.log(JSON.stringify(event));
      return Response.json(event,{status:409});
    }
    if(prepared.http!==200||!/^[a-f0-9]{64}$/.test(prepared.sha256)) throw Error("UMS_PREPARE_DENIED");
    const authorization=await append(env,id+":read",prepared.sha256,null,UMS);
    const read=await gateway("read",id,UMS,prepared.sha256);
    if(read.http!==200||read.sha256!==prepared.sha256||
       await digest(JSON.stringify(read.bundle))!==prepared.sha256) throw Error("KNOWLEDGE_HASH_REJECTED");
    const rule=read.bundle.items.find(x=>x.knowledge_id==="RULE:UMS-001-LICENSE-PROVENANCE-QA")?.payload;
    if(rule?.gate!=="LICENSE_PROVENANCE_QA"||rule.licensing_baseline?.source_provenance_required!==true) throw Error("UMS_RULE_REQUIRED");
    const decision=evaluateIdentityRights({identity_type:"FICTIONAL_LICENSED",rights_record:null});
    if(decision.decision!=="HUMAN_REQUIRED") throw Error("UMS_DECISION_UNEXPECTED");
    const resultHash=await digest(JSON.stringify({decision,source_id:rule.source_id,source_version:rule.source_version}));
    const audit=await append(env,id+":decision",resultHash,null,UMS);
    const persisted=await ledger(env,UMS).read(id+":decision");
    if(persisted.records.length!==1||persisted.records[0].recorded_at!==audit.recorded_at) throw Error("AUDIT_VERIFY_FAILED");
    const event={status:"UMS_CONSUMED_KNOWLEDGE",request_id:id,consumer_id:UMS.subagent_id,
      knowledge_sha256:read.sha256,decision:decision.decision,decision_sha256:resultHash,
      audit_read:authorization.status,audit_decision:audit.status,audit_recorded_at:audit.recorded_at,
      external_actions:0,certified:0};
    console.log(JSON.stringify(event));
    return Response.json(event);
  }catch{
    console.log(JSON.stringify({status:"UMS_BLOCKED",request_id:id}));
    return Response.json({status:"UMS_BLOCKED"},{status:503});
  }
}

export default {
  fetch(request,env){
    const url=new URL(request.url);
    if(request.method!=="POST"||url.origin!=="https://cerebro-knowledge-agent-bridge-lab.carlosj-munozcabeza.workers.dev"||url.pathname!=="/ums"||url.search) return new Response(null,{status:404});
    return runUms(request,env);
  },
  async queue(batch,env){
    if(batch.queue!==QUEUE) return;
    for(const m of batch.messages){
      const {type,id}=m.body??{};
      if(!allowed.has(type)||typeof id!=="string"||!idPattern.test(id)){m.retry();continue;}
      try {
        const v=type==="RUN"?await execute(env,id):type==="NEGATIVES"?await negatives(env,id):
          {result:"AGENT_AUDIT_VERIFY",request_id:id,read:(await ledger(env).read(id+":read")).records.length,
            decision:(await ledger(env).read(id+":decision")).records.length};
        console.log(JSON.stringify(v));
      } catch(error) {
        const message=String(error?.message??"");
        console.log(JSON.stringify({result:"AGENT_FAIL",request_id:id,
          code:/^[A-Z0-9_]{1,90}$/.test(message)?message:"INTERNAL_OR_AUDIT_FAILURE"}));
      }
      m.ack();
    }
  }
};