// TECH-SCOUT · parallel private LAB Gateway · single bounded queue trigger.
const EXPECTED_QUEUE = "cerebro-techscout-gateway-one-shot-lab-eu";
const TARGET = Object.freeze({company_id:"fenix-capital",engine_id:"TECH-SCOUT",environment:"LAB",version:"0.1.0",capability:"TECHSCOUT.PROBE"});
const VALID_ID = /^techscout_[a-z0-9_-]{16,56}$/;
function check(obj){
 if(!obj || typeof obj!=="object" || Array.isArray(obj)) return false;
 const keys=["company_id","engine_id","environment","version","capability","provider","request_id"];
 if(Object.keys(obj).length!==keys.length||Object.keys(obj).some(k=>!keys.includes(k))) return false;
 return Object.keys(TARGET).every(k=>obj[k]===TARGET[k]) && ["WORLD_BANK","QUICKCHART","COMMONS","GDELT"].includes(obj.provider) && typeof obj.request_id==="string" && VALID_ID.test(obj.request_id);
}
function small(s){return String(s||"").slice(0,60).replace(/[^a-zA-Z0-9_ -]/g,"_")}
export default {
 async fetch(){return new Response("TECHSCOUT_LAB_PRIVATE_DISABLED",{status:403,headers:{"content-type":"text/plain","cache-control":"no-store"}})},
 async queue(batch,env){
  if(batch.queue!==EXPECTED_QUEUE)throw Error("QUEUE_DENIED");
  const active=env.TECHSCOUT_GATEWAY_ENABLED==="true"&&env.LAB_KV&&env.TECHSCOUT&&typeof env.TECHSCOUT_CALLER_TOKEN==="string";
  for(const message of batch.messages){
   if(!active){message.retry({delaySeconds:60});continue}
   const body=message.body;
   if(!check(body)){message.ack();continue}
   const key="techscout/gateway/v0.1.0/"+body.request_id;
   const before=await env.LAB_KV.get(key);
   if(before!==null){message.ack();continue}
   const base={company_id:body.company_id,engine_id:body.engine_id,environment:"LAB",capability:body.capability,provider:body.provider,request_id:body.request_id,processed_by:"techscout_parallel_gateway_lab"};
   try{await env.LAB_KV.put(key,JSON.stringify({...base,status:"GATEWAY_STARTED",at:Date.now()}),{expirationTtl:86400*7})}
   catch{message.retry({delaySeconds:60});continue}
   let result;
   try{result=await env.TECHSCOUT.probePublic(body,env.TECHSCOUT_CALLER_TOKEN)}
   catch(e){result={status:"BLOCKED",reason:"SERVICE_RPC_FAILED",kind:small(e.name)}}
   const record={...base,status:result?.status||"BLOCKED",reason:small(result?.reason),http:result?.http||null,shape_ok:result?.shape_ok===true,at:Date.now()};
   try{await env.LAB_KV.put(key,JSON.stringify(record),{expirationTtl:86400*7});message.ack()}
   catch{message.retry({delaySeconds:60})}
  }
 }
};
