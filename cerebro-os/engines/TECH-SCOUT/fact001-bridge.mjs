// FACT001 / TECH-SCOUT: isolated read-only bridge. Existing NIA and UMS paths unchanged.
const FIXED=Object.freeze({company_id:'fenix-capital',engine_id:'TECH-SCOUT',environment:'LAB',version:'0.1.0',capability:'TECHSCOUT.PROBE'});
const FIELDS=Object.freeze([...Object.keys(FIXED),'provider','request_id']);
const PROVIDERS=new Set(['WORLD_BANK','QUICKCHART','COMMONS','GDELT']);
const PREFIX='techscout/fact001/v0.1.0/';
export const FACT_TECHSCOUT_QUEUE='cerebro-techscout-fact001-e2e-lab-eu';
export function validateFactTechscout(command){
 if(!command||typeof command!=='object'||Array.isArray(command))return 'INVALID_BODY';
 const keys=Object.keys(command);
 if(keys.length!==FIELDS.length||keys.some(x=>!FIELDS.includes(x)))return 'UNEXPECTED_FIELD';
 for(const [k,v] of Object.entries(FIXED))if(command[k]!==v)return 'SCOPE_DENIED';
 if(!PROVIDERS.has(command.provider))return 'PROVIDER_DENIED';
 if(typeof command.request_id!=='string'||!/^techscout_[a-z0-9_-]{16,56}$/.test(command.request_id))return 'REQUEST_ID_DENIED';
 return null;
}
export async function factTechscoutProbe(env,command){
 if(env?.TECHSCOUT_FACT001_ENABLED!=='true')return {status:'DISABLED',reason:'FACT001_OFF'};
 const error=validateFactTechscout(command);
 if(error)return {status:'DENIED',reason:error};
 if(!env.TECHSCOUT||typeof env.TECHSCOUT.probePublic!=='function'||typeof env.TECHSCOUT_CALLER_TOKEN!=='string'||env.TECHSCOUT_CALLER_TOKEN.length<48)return {status:'BLOCKED',reason:'RPC_NOT_READY'};
 if(!env.LAB_KV||typeof env.LAB_KV.get!=='function'||typeof env.LAB_KV.put!=='function')return{status:'BLOCKED',reason:'AUDIT_NOT_READY'};
 const key=PREFIX+command.request_id;
 try{
  const prior=await env.LAB_KV.get(key);
  if(prior!==null)return {status:'DUPLICATE',reason:'RECEIPT_EXISTS'};
  const meta={request_id:command.request_id,company_id:FIXED.company_id,engine_id:FIXED.engine_id,environment:'LAB',provider:command.provider,route:'FACT001_PRIVATE_TECHSCOUT',ts:Date.now()};
  await env.LAB_KV.put(key,JSON.stringify({...meta,status:'STARTED'}),{expirationTtl:604800});
  let response;
  try{response=await env.TECHSCOUT.probePublic(command,env.TECHSCOUT_CALLER_TOKEN);}
  catch{response={status:'DEGRADED',reason:'WORKER_RPC_FAILURE'};}
  const status=response?.status==='PASS'&&response?.http===200&&response?.shape_ok===true?'PASS':'DEGRADED';
  const receipt={...meta,status,http:Number.isInteger(response?.http)?response.http:null,reason:String(response?.reason||'').slice(0,60)};
  await env.LAB_KV.put(key,JSON.stringify(receipt),{expirationTtl:604800});
  return {status,provider:command.provider,request_id:command.request_id,receipt_key:key,http:receipt.http};
 }catch{return {status:'BLOCKED',reason:'AUDIT_FAILURE'};}
}
