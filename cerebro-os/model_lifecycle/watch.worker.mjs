/**
 * CEREBRO OS · shared FACT-001 / SUP-001 model lifecycle watcher · LAB v0.
 * Read official retirement notices, compare the registered engines and write KV receipts.
 * NO model calls, GitHub mutations, deployments, publication, money or customer data.
 */
export const POLICY=Object.freeze({
  version:"0.1.0",engine_id:"SUP-001",environment:"LAB",
  canonical:"https://developers.cloudflare.com/changelog/post/2026-11-05-planned-model-deprecations/",
  feed:"https://developers.cloudflare.com/changelog/rss/index.xml",
  max_docs:5,max_bytes:250000,model_calls_allowed:0,paid_inference_allowed:false,
  autonomous_promotion:false,publish_allowed:false
});
const ROOT="https://developers.cloudflare.com/changelog/post/";
const MODEL=/^@(cf|hf)\/[a-z0-9][a-z0-9._-]*(?:\/[a-z0-9][a-z0-9._-]*){1,3}$/;
const MONTHS={january:0,february:1,march:2,april:3,may:4,june:5,july:6,august:7,september:8,october:9,november:10,december:11};
const dateISO=x=>{
 const m=String(x).match(/^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d\d)$/i);
 if(!m)return null;
 const y=Number(m[3]),month=MONTHS[m[1].toLowerCase()],day=Number(m[2]),dt=new Date(Date.UTC(y,month,day));
 return dt.getUTCFullYear()===y&&dt.getUTCMonth()===month&&dt.getUTCDate()===day?dt.toISOString().slice(0,10):null;
};
export function parseNotices(content,url){
 if(typeof content!=="string"||content.length>POLICY.max_bytes||!url.startsWith(ROOT)||!url.endsWith("/"))return [];
 const result=[];let active=null;
 for(const original of content.split(/\r?\n/)){
  const line=original.trim(),h=line.match(/^(#{1,6})\s+(.+)$/);
  if(h){
   const m=h[2].match(/^Models? deprecated on\s+(.+)$/i);
   if(m){const d=dateISO(m[1]);active=d?{source_url:url,deprecated_on:d,model_ids:[],level:h[1].length}:null;if(active)result.push(active);}
   else if(active&&(h[1].length<active.level||(h[1].length===active.level&&!/^(LLMs|Other models)$/i.test(h[2]))))active=null;
   continue;
  }
  if(!active||!/^[-*]\s+/.test(line))continue;
  const id=line.match(/^[-*]\s+\x60(@(?:cf|hf)\/[a-z0-9._/-]+)\x60/i)?.[1];
  if(id&&MODEL.test(id)&&!active.model_ids.includes(id))active.model_ids.push(id);
 }
 return result.filter(x=>x.model_ids.length).map(({level,...other})=>other);
}
export function officialNoticeLinks(feed){
 if(typeof feed!=="string"||feed.length>POLICY.max_bytes)return [];
 const urls=feed.match(/https:\/\/developers\.cloudflare\.com\/changelog\/post\/[a-z0-9-]+\//g)||[];
 return [...new Set(urls)].filter(x=>/model.*deprecat|deprecat.*model/.test(x)).slice(0,POLICY.max_docs);
}
export function matchRetirements(notices,inventory,now=new Date()){
 if(!Array.isArray(notices)||!Array.isArray(inventory)||!Number.isFinite(now.getTime()))throw Error("BAD_INPUT");
 const events=[];
 for(const engine of inventory){
  if(!engine||!engine.company_id||!engine.engine_id||!engine.version||!engine.worker||
     !["LAB","PREPROD","PROD"].includes(engine.environment)||!Array.isArray(engine.models))
   throw Error("INVENTORY_CONTRACT");
  for(const m of engine.models){
   if(!MODEL.test(m.model_id)||!["generator","reviewer","arbiter","embedding","other"].includes(m.role))throw Error("MODEL_CONTRACT");
   for(const n of notices){
    if(!n.model_ids.includes(m.model_id))continue;
    events.push({company_id:engine.company_id,engine_id:engine.engine_id,
      environment:engine.environment,version:engine.version,worker:engine.worker,
      role:m.role,model_id:m.model_id,deprecated_on:n.deprecated_on,
      days_remaining:Math.floor((Date.parse(n.deprecated_on+"T00:00:00Z")-now.getTime())/86400000),
      source:n.source_url,state:"PATCH_REQUIRED_LAB",
      automatic_actions_allowed:["DISCOVER","PREPARE_PATCH","RUN_OFFLINE_TESTS"],
      publish_allowed:false,deploy_allowed:false,
      required_gates:["INVENTORY","DEPENDENCIES","BACKUP","OLD_VS_NEW","TESTS","E2E","COST_HARD_STOP","TRIBUNAL","OBSERVABILITY","ROLLBACK","PREPROD"]});
   }
  }
 }
 return events.sort((a,b)=>a.deprecated_on.localeCompare(b.deprecated_on)||a.worker.localeCompare(b.worker));
}
// Fallback covers the three physically verified LAB workers; FACT enrollment must keep KV registry current.
export const SEED_REGISTRY=[
 {company_id:"fenix-capital",engine_id:"SOC-FB-FINANCIAL-REAL-ESTATE-V1",environment:"LAB",version:"0.1.0",worker:"cerebro-facebook-knowledge-autoqual-lab-eu",models:[{role:"generator",model_id:"@cf/google/gemma-4-26b-a4b-it"},{role:"reviewer",model_id:"@cf/qwen/qwen2.5-coder-32b-instruct"}]},
 {company_id:"fenix-capital",engine_id:"SOC-IG-FINANCIAL-REAL-ESTATE-V1",environment:"LAB",version:"0.1.0",worker:"cerebro-instagram-knowledge-autoqual-lab-eu",models:[{role:"generator",model_id:"@cf/google/gemma-4-26b-a4b-it"},{role:"reviewer",model_id:"@cf/qwen/qwen2.5-coder-32b-instruct"}]},
 {company_id:"fenix-capital",engine_id:"SOC-LI-FINANCIAL-REAL-ESTATE-V1",environment:"LAB",version:"0.1.0",worker:"cerebro-linkedin-autonomy-ticker-lab-eu",models:[{role:"generator",model_id:"@cf/google/gemma-4-26b-a4b-it"},{role:"reviewer",model_id:"@cf/qwen/qwen2.5-coder-32b-instruct"}]}
];
async function readOfficial(url){
 const p=new URL(url);
 if(p.protocol!=="https:"||p.hostname!=="developers.cloudflare.com"||
    !(p.pathname==="/changelog/rss/index.xml"||/^\/changelog\/post\/[a-z0-9-]+\/index\.md$/.test(p.pathname)))
  throw Error("UNTRUSTED_SOURCE");
 const r=await fetch(p.toString(),{method:"GET",redirect:"error",headers:{Accept:"text/plain,application/xml,text/markdown"}});
 if(!r.ok)throw Error("OFFICIAL_HTTP_"+r.status);
 const s=await r.text();
 if(s.length>POLICY.max_bytes)throw Error("OFFICIAL_SIZE_LIMIT");
 return s;
}
export async function scan(env,now=new Date()){
 if(!env?.LIFECYCLE_KV||env.LAB_READONLY!=="true"||env.COMPANY_SCOPE!=="GLOBAL")throw Error("LAB_SCOPE_DENIED");
 const key="model-lifecycle/v0/",today=now.toISOString().slice(0,10);
 const registered=await env.LIFECYCLE_KV.get(key+"registry","json");
 const inventory=Array.isArray(registered)?registered:SEED_REGISTRY;
 const urls=[POLICY.canonical],errors=[],notices=[];
 try{urls.push(...officialNoticeLinks(await readOfficial(POLICY.feed)))}catch{errors.push("FEED_UNAVAILABLE");}
 const distinct=[...new Set(urls)].slice(0,POLICY.max_docs);
 for(const u of distinct){
  try{notices.push(...parseNotices(await readOfficial(u+"index.md"),u));}
  catch{errors.push("OFFICIAL_NOTICE_UNAVAILABLE");}
 }
 const affected=matchRetirements(notices,inventory,now);
 const state=errors.length?"DEGRADED_HOLD":affected.length?"PATCH_REQUIRED_LAB":"NO_KNOWN_MATCH";
 const receipt={schema:"CEREBRO_MODEL_LIFECYCLE_SCAN_V0",company_id:"GLOBAL",engine_id:"SUP-001",
   environment:"LAB",version:POLICY.version,scan_date:today,state,
   source_urls:distinct,notices_count:notices.length,registered_engines:inventory.length,
   affected,errors,model_calls:0,cost_eur:0,autonomous_promotion:false,publish_allowed:false};
 await env.LIFECYCLE_KV.put(key+"last-scan",JSON.stringify(receipt));
 await env.LIFECYCLE_KV.put(key+"history/"+today,JSON.stringify(receipt),{expirationTtl:2592000});
 console.log(JSON.stringify({event:"MODEL_RETIREMENT_SCAN_RECEIPT",date:today,state,
  affected:affected.length,errors:errors.length}));
 return receipt;
}
export default {
 async fetch(){return new Response(null,{status:404,headers:{"Cache-Control":"no-store"}});},
 async scheduled(_controller,env,ctx){
  ctx.waitUntil(scan(env).catch(e=>console.error(JSON.stringify({
   event:"MODEL_RETIREMENT_SCAN_FAILURE",error:String(e.message||e).slice(0,120)}))));
 }
};
