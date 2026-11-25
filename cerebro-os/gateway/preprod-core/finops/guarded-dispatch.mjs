// Dispatcher retains its existing signing key and Workflow bindings. The separate DO
// is reservation-only. No key or execution binding crosses this boundary.
import {dispatchCore} from './core-dispatch.mjs';
const idOK=id=>typeof id==='string'&&/^CORE-PREPROD-20261124-00[2-8]$/.test(id);
const blocked=reason=>({status:'HOLD',reason,dispatch_allowed:false,promotion_allowed:false});
export async function submitGuarded(e,id){
 if(!idOK(id)||e.CORE_ENV!=='PREPROD'||e.CORE_FINOPS_ENABLED!=='true'||!/^[a-f0-9]{32}$/.test(e.CORE_FINOPS_ACCOUNT??''))return blocked('FINOPS_SCOPE_DENIED');
 let r;
 try{
  const ns=e.CORE_FINOPS_LEDGER.jurisdiction('eu');
  r=await ns.get(ns.idFromName('core-finops-preprod:'+e.CORE_FINOPS_ACCOUNT)).reserve(id);
 }catch{return blocked('FINOPS_PORT_UNAVAILABLE_NO_RETRY');}
 if(r?.status==='DEFER'&&Number.isSafeInteger(r.retry_after_epoch)&&r.retry_after_epoch>Math.floor(Date.now()/1000)&&r.retry_after_epoch<=Math.floor(Date.now()/1000)+86400&&r.promotion_allowed===false&&r.dispatch_allowed===false)return r;
 if(r?.status!=='RESERVED'||r.reason!=='NATIVE_FREE_RESERVATION'||r.account_id!==e.CORE_FINOPS_ACCOUNT||r.request_id!==id||r.promotion_allowed!==false||r.dispatch_allowed!==false||Object.keys(r).sort().join('|')!=='account_id|dispatch_allowed|promotion_allowed|reason|request_id|status')return blocked(r?.status==='HOLD'&&typeof r.reason==='string'&&/^[A-Z_]{1,80}$/.test(r.reason)?r.reason:'FINOPS_RESULT_DENIED');
 try{
  const out=await dispatchCore(e,id);
  if(out?.request_id!==id||out?.instance_id!==id.toLowerCase())return blocked('SUBMISSION_AMBIGUOUS_NO_RETRY');
  return {status:'SUBMITTED',reason:'NATIVE_FREE_AND_REMOTE_RESERVATION',request_id:id,instance_id:out.instance_id,dispatch_allowed:false,promotion_allowed:false};
 }catch{return blocked('SUBMISSION_FAILED_RECONCILE_NO_RETRY');}
}
