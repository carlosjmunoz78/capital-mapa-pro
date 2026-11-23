// ZEUS native FACT-001 P5 monitor, shared-runtime module (LAB only).
// No HTTP entrypoint, no cron, no external API, no job retries/mutations.
export const SCOPE = Object.freeze({
 company_id: 'fenix-capital', engine_id: 'FACT-001',
 environment: 'LAB', version: '1.0.0'
});
const AUTOMATION='FACT001_P5_DAILY_READ_V1';
const PREFIX='FACT001-P5-';
const HEALTH_TABLE='zeus_fact_p5_health_v1';

export function evaluateP5Health({registry,job,newReconcileCount=0,dayKey}) {
 const requestId=PREFIX+dayKey;
 let code='GREEN';
 if(!registry || Number(registry.enabled)!==1 || Number(registry.max_daily_jobs)!==1 ||
    registry.company_id!==SCOPE.company_id || registry.engine_id!==SCOPE.engine_id ||
    registry.environment!==SCOPE.environment || registry.version!==SCOPE.version) {
   code='AUTOMATION_DRIFT';
 } else if(!job || job.request_id!==requestId || job.company_id!==SCOPE.company_id ||
           job.engine_id!==SCOPE.engine_id || job.environment!==SCOPE.environment) {
   code='DAILY_JOB_MISSING_OR_SCOPE_INVALID';
 } else if(job.state!=='COMPLETED' || Number(job.attempts)!==1) {
   code='DAILY_JOB_NOT_COMPLETED';
 } else if(Number(job.max_cost_eur)!==0 || Number(job.result_valid)!==1) {
   code='RECEIPT_OR_COST_INVALID';
 } else if(Number(newReconcileCount)>0) {
   code='NEW_RECONCILE';
 }
 return {state:code==='GREEN'?'GREEN':'BLOCKED',code,request_id:requestId,
         company_id:SCOPE.company_id,engine_id:SCOPE.engine_id,
         environment:SCOPE.environment,version:SCOPE.version,
         next_action:code==='GREEN'?'NONE':'SUPERVISOR_REVIEW',
         human_required:false,external_mutation_allowed:false,cost_ceiling_eur:0};
}
function dayKeyUTC(ms) { return new Date(ms).toISOString().slice(0,10).replace(/-/g,''); }

export async function superviseP5Daily(env, scheduledTime=Date.now()) {
 if(env?.ZEUS_P5_MONITOR_ENABLED!=='true' || !env?.RECOVERY_DB) return {status:'OFF'};
 if(!Number.isFinite(scheduledTime) || scheduledTime<0) throw new Error('invalid scheduledTime');
 const date=new Date(scheduledTime);
 // After the daily FACT job; do not mark the midnight dispatch as missing.
 if(date.getUTCHours()<2) return {status:'NOT_DUE'};
 const dayKey=dayKeyUTC(scheduledTime), requestId=PREFIX+dayKey;
 const receiptId='ZEUS-P5-'+dayKey+'-fenix-capital-LAB';
 const db=env.RECOVERY_DB;
 const existing=await db.prepare(
   'SELECT receipt_id,state,code FROM '+HEALTH_TABLE+' WHERE receipt_id=?1'
 ).bind(receiptId).first();
 if(existing) return {status:'ALREADY_RECORDED',receipt_id:receiptId,
                     state:existing.state,code:existing.code};
 const [registry,job,reconcile]=await Promise.all([
   db.prepare(
     'SELECT company_id,engine_id,environment,version,enabled,max_daily_jobs FROM fact001_p5_automation_registry_v1 WHERE automation_id=?1 LIMIT 1'
   ).bind(AUTOMATION).first(),
   db.prepare(
     'SELECT request_id,company_id,engine_id,environment,version,state,attempts,max_cost_eur,json_valid(result_json) AS result_valid FROM fact001_p5_jobs_v1 WHERE request_id=?1 LIMIT 1'
   ).bind(requestId).first(),
   db.prepare(
     "SELECT COUNT(*) AS n FROM fact001_p5_jobs_v1 WHERE day_key>=?1 AND state='RECONCILE'"
   ).bind(dayKey).first()
 ]);
 const report=evaluateP5Health({registry,job,newReconcileCount:reconcile?.n??0,dayKey});
 const fingerprint=JSON.stringify(report);
 const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(fingerprint)));
 const digest=Array.from(hash,x=>x.toString(16).padStart(2,'0')).join('');
 await db.prepare(
   'INSERT INTO '+HEALTH_TABLE+' (receipt_id,company_id,engine_id,environment,version,day_key,request_id,state,code,observed_at_ms,fingerprint_sha256,source) '+
   "VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,'ZEUS_P5_SHARED_RUNTIME') ON CONFLICT(receipt_id) DO NOTHING"
 ).bind(receiptId,report.company_id,report.engine_id,report.environment,
        report.version,dayKey,requestId,report.state,report.code,scheduledTime,digest).run();
 const stored=await db.prepare(
   'SELECT receipt_id,state,code,fingerprint_sha256 FROM '+HEALTH_TABLE+' WHERE receipt_id=?1'
 ).bind(receiptId).first();
 if(!stored || stored.fingerprint_sha256!==digest || stored.state!==report.state ||
    stored.code!==report.code) throw new Error('ZEUS_P5_JOURNAL_CONFLICT');
 return {status:'RECORDED',receipt_id:receiptId,state:report.state,
         code:report.code,scope:'LAB',external_mutation_allowed:false};
}
