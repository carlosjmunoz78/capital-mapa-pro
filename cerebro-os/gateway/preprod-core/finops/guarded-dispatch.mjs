// Private account ledger in the dispatcher runtime. No public HTTP or paid fallback.
import {DurableObject} from 'cloudflare:workers';
import {createGuard} from './zero-cost-guard.mjs';
import {dispatchCore} from './core-dispatch.mjs';
const idOK=id=>typeof id==='string'&&/^CORE-PREPROD-20261124-00[2-8]$/.test(id);
const blocked=reason=>({status:'HOLD',reason,dispatch_allowed:false,promotion_allowed:false});
export class CoreFinOpsLedger extends DurableObject {
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;}
 async submit(id){
  const e=this.e;
  if(!idOK(id)||e.CORE_ENV!=='PREPROD'||e.CORE_FINOPS_ENABLED!=='true')return blocked('FINOPS_SCOPE_DENIED');
  // Only administrative runtime bindings may supply the plan observation.
  // A missing or stale observation is never silently refreshed.
  try{
   const g=createGuard({storage:this.storage,accountId:e.CORE_FINOPS_ACCOUNT,
    readTrustedPlan:async()=>JSON.parse(e.CORE_FINOPS_PLAN),
    dailyLimit:Number(e.CORE_FINOPS_DAILY_LIMIT)});
   return await g.submit({company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ',request_id:id},i=>dispatchCore(e,i));
  }catch{return blocked('FINOPS_CONFIG_OR_LEDGER_UNAVAILABLE');}
 }
}
export async function submitGuarded(e,id){
 if(!idOK(id)||e.CORE_ENV!=='PREPROD'||e.CORE_FINOPS_ENABLED!=='true'||!/^[a-f0-9]{32}$/.test(e.CORE_FINOPS_ACCOUNT??''))return blocked('FINOPS_SCOPE_DENIED');
 try{
  const ns=e.CORE_FINOPS_LEDGER.jurisdiction('eu');
  const stub=ns.get(ns.idFromName('core-finops-preprod:'+e.CORE_FINOPS_ACCOUNT));
  const r=await stub.submit(id);
  if(r?.status==='SUBMITTED'&&r.request_id===id&&r.instance_id===id.toLowerCase()&&r.promotion_allowed===false)return r;
  if(r?.status==='DEFER'&&Number.isSafeInteger(r.retry_after_epoch)&&r.retry_after_epoch>Math.floor(Date.now()/1000)&&r.retry_after_epoch<=Math.floor(Date.now()/1000)+86400&&r.promotion_allowed===false)return r;
  return blocked(r?.status==='HOLD'&&typeof r.reason==='string'&&/^[A-Z_]{1,80}$/.test(r.reason)?r.reason:'FINOPS_RESULT_DENIED');
 }catch{return blocked('FINOPS_PORT_UNAVAILABLE_NO_RETRY');}
}
