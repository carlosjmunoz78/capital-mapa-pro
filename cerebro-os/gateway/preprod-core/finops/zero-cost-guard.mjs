// Additive PREPROD guard; native Workers Free enforcement remains primary.
// Runtime configuration and clock are trusted inputs, never request fields.
const DAY=86400;
const idPattern=/^CORE-PREPROD-20261124-00[2-8]$/;
const planAge=86400;
const maxDailyOrders=8; // internal ceiling for the existing finite rehearsal scope, NOT a provider quota.
const scope={company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ'};
const keys=['account_id','plan','observed_at_epoch','source','products','external_paid_services'];
const products=['workers','durable_objects_sqlite','workflows'];
const result=(status,reason,extra={})=>({status,reason,dispatch_allowed:false,promotion_allowed:false,...extra});
// Standing owner authorization is not a fresh provider observation. Restricted to the
// existing finite PREPROD inventory rehearsal, never used to attest PROD billing.
const STANDING='OWNER_FREE_REHEARSAL_V1';
const attestationSource='owner-attestation-2026-11-25-and-ZEUS-CP181-1008';
function validPlan(p,account,now,mode){
 return p&&typeof p==='object'&&Object.keys(p).sort().join('|')===keys.slice().sort().join('|')&&
 /^[a-f0-9]{32}$/.test(account)&&p.account_id===account&&p.plan==='WORKERS_FREE'&&
 Number.isSafeInteger(p.observed_at_epoch)&&p.observed_at_epoch>=0&&p.observed_at_epoch<=now&&(now-p.observed_at_epoch<planAge||(mode===STANDING&&p.source===attestationSource&&p.observed_at_epoch===1795600325))&&
 typeof p.source==='string'&&p.source.length>=8&&p.source.length<=256&&
 Array.isArray(p.products)&&p.products.slice().sort().join('|')===products.slice().sort().join('|')&&
 p.external_paid_services===false;
}
function validOrder(order){
 return order&&Object.keys(order).length===Object.keys(scope).length+1&&Object.entries(scope).every(([k,v])=>order[k]===v)&&
 typeof order.request_id==='string'&&idPattern.test(order.request_id);
}
// Use a single account-level serialized SQL ledger; no per-order/per-tenant quota silos.
// Reserve before dispatch; never refund an ambiguous or completed submission.
export function createReservationGuard({storage,accountId,readTrustedPlan,clock=()=>Math.floor(Date.now()/1000),dailyLimit=maxDailyOrders,policyMode='FRESH_OBSERVATION'}){
 if(!storage?.sql||typeof storage.transactionSync!=='function'||typeof readTrustedPlan!=='function'||
 !/^[a-f0-9]{32}$/.test(accountId)||!['FRESH_OBSERVATION',STANDING].includes(policyMode)||!Number.isSafeInteger(dailyLimit)||dailyLimit<1||dailyLimit>maxDailyOrders)throw Error('FINOPS_CONFIG_DENIED');
 const sql=storage.sql;
 sql.exec("CREATE TABLE IF NOT EXISTS core_finops_reservations (account_id TEXT NOT NULL, request_id TEXT NOT NULL, day INTEGER NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(account_id,request_id))");
 return Object.freeze({async reserve(order){
   if(!validOrder(order))return result('BLOCKED','SCOPE_DENIED');
   const id=order.request_id;
   try{
     const p=await readTrustedPlan();
     const now=clock();
     if(!Number.isSafeInteger(now)||now<0||!validPlan(p,accountId,now,policyMode))return result('HOLD','FREE_PLAN_UNVERIFIED');
     const day=Math.floor(now/DAY);
     const reserved=storage.transactionSync(()=>{
       if(sql.exec('SELECT request_id FROM core_finops_reservations WHERE account_id=? AND request_id=?',accountId,id).toArray().length)return 'DUPLICATE';
       const n=sql.exec('SELECT COUNT(*) AS n FROM core_finops_reservations WHERE account_id=? AND day=?',accountId,day).toArray()[0]?.n;
       if(!Number.isSafeInteger(n)||n<0)throw Error('LEDGER_INVALID');
       if(n>=dailyLimit)return 'QUOTA';
       sql.exec('INSERT INTO core_finops_reservations VALUES (?,?,?,?)',accountId,id,day,now);
       return 'RESERVED';
     });
     if(reserved==='DUPLICATE')return result('HOLD','DUPLICATE_RECONCILE_NO_RETRY');
     if(reserved==='QUOTA')return result('DEFER','INTERNAL_DAILY_LIMIT',{retry_after_epoch:(day+1)*DAY});
     return result('RESERVED','NATIVE_FREE_RESERVATION',{request_id:id,account_id:accountId});
   }catch{return result('HOLD','PLAN_OR_LEDGER_UNAVAILABLE');}
 }});
}
// Compatibility wrapper retains the original one-shot contract; reservation is never
// refunded after transport ambiguity. The separate ledger uses reserve only.
export function createGuard(config){
 const ledger=createReservationGuard(config);
 return Object.freeze({async submit(order,dispatch){
  if(typeof dispatch!=='function')return result('BLOCKED','SCOPE_DENIED');
  const r=await ledger.reserve(order);
  if(r.status!=='RESERVED')return r;
  try{
   const response=await dispatch(order.request_id);
   if(response?.request_id!==order.request_id||response?.instance_id!==order.request_id.toLowerCase())return result('HOLD','SUBMISSION_AMBIGUOUS_NO_RETRY');
   return result('SUBMITTED','NATIVE_FREE_AND_LOCAL_RESERVATION',{request_id:order.request_id,instance_id:response.instance_id});
  }catch{return result('HOLD','SUBMISSION_FAILED_RECONCILE_NO_RETRY');}
 }});
}
