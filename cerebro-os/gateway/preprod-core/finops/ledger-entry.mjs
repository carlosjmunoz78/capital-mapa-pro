// Dedicated, private PREPROD FinOps ledger. No execution credentials, Workflows or network.
import {DurableObject} from 'cloudflare:workers';
import {createReservationGuard} from './zero-cost-guard.mjs';
const blocked=reason=>({status:'HOLD',reason,dispatch_allowed:false,promotion_allowed:false});
export default {fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}})}};
export class CoreFinOpsLedger extends DurableObject {
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;}
 async reserve(id){
  const e=this.e;
  if(typeof id!=='string'||!/^CORE-PREPROD-20261124-00[2-8]$/.test(id)||e.CORE_ENV!=='PREPROD'||e.CORE_FINOPS_ENABLED!=='true')return blocked('FINOPS_SCOPE_DENIED');
  try{
   const g=createReservationGuard({storage:this.storage,accountId:e.CORE_FINOPS_ACCOUNT,
    readTrustedPlan:async()=>JSON.parse(e.CORE_FINOPS_PLAN),
    dailyLimit:Number(e.CORE_FINOPS_DAILY_LIMIT),policyMode:e.CORE_FINOPS_POLICY_MODE??'FRESH_OBSERVATION'});
   return await g.reserve({company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ',request_id:id});
  }catch{return blocked('FINOPS_CONFIG_OR_LEDGER_UNAVAILABLE');}
 }
}
