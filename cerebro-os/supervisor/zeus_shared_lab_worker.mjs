// CEREBRO OS · ZEUS shared supervisor · CP86 LAB. No remote fetch route or mutation of engine jobs.
export const VERSION="0.1.0";
export const CHECKS=Object.freeze([{check_id:"FACT001_P5_DAILY_READ_V1",company_id:"fenix-capital",engine_id:"FACT-001",environment:"LAB",version:"1.0.0",automation_id:"FACT001_P5_DAILY_READ_V1",operation:"providers.five.inventory.read"}]);
const BASELINE="FACT001-P5-20261112";
const DAY_MS=86400000;
export function utcDay(ms){if(!Number.isFinite(ms)||ms<0)throw Error("INVALID_CLOCK");return new Date(ms).toISOString().slice(0,10).replaceAll("-","");}
export function classifyP5({config,job,newReconciles},check){
  const validConfig=!!config&&config.automation_id===check.automation_id&&config.company_id===check.company_id&&config.engine_id===check.engine_id&&config.environment===check.environment&&config.version===check.version&&config.enabled===1&&config.max_daily_jobs===1;
  if(!validConfig)return {status:"INCIDENT",code:"AUTOMATION_CONFIG_DRIFT"};
  if(!Number.isInteger(newReconciles)||newReconciles<0)return {status:"INCIDENT",code:"RECONCILE_QUERY_INVALID"};
  if(newReconciles>0)return {status:"INCIDENT",code:"NEW_RECONCILE"};
  if(!job)return {status:"INCIDENT",code:"P5_DAILY_MISSING"};
  if(job.request_id!=="FACT001-P5-"+job.day_key||job.company_id!==check.company_id||job.engine_id!==check.engine_id||job.environment!==check.environment||job.version!==check.version||job.operation!==check.operation||job.max_cost_eur!==0)return {status:"INCIDENT",code:"JOB_SCOPE_DRIFT"};
  if(job.state!=="COMPLETED")return {status:"INCIDENT",code:"P5_NOT_COMPLETED"};
  if(job.attempts!==1||!Number.isSafeInteger(job.completed_at_ms)||job.completed_at_ms<0)return {status:"INCIDENT",code:"P5_COMPLETION_UNVERIFIED"};
  return {status:"HEALTHY",code:"P5_DAILY_COMPLETED"};
}
function q(db,sql,args=[]){return db.prepare(sql).bind(...args).first();}
export async function observeCheck(db,check,ms){
  if(check.environment!=="LAB"||check.engine_id!=="FACT-001"||check.company_id!=="fenix-capital")throw Error("SCOPE_DENIED");
  const day=utcDay(ms),request_id="FACT001-P5-"+day;
  const config=await q(db,"SELECT automation_id,company_id,engine_id,environment,version,enabled,max_daily_jobs FROM fact001_p5_automation_registry_v1 WHERE automation_id=?1",[check.automation_id]);
  const job=await q(db,"SELECT request_id,day_key,company_id,engine_id,environment,version,operation,max_cost_eur,state,attempts,completed_at_ms FROM fact001_p5_jobs_v1 WHERE request_id=?1",[request_id]);
  const other=await q(db,"SELECT COUNT(*) AS n FROM fact001_p5_jobs_v1 WHERE company_id=?1 AND engine_id=?2 AND environment='LAB' AND state='RECONCILE' AND request_id<>?3",[check.company_id,check.engine_id,BASELINE]);
  const status=classifyP5({config,job,newReconciles:Number(other?.n)},check);
  return {schema:"cerebro.zeus.supervisor.v1",check_id:check.check_id,company_id:check.company_id,engine_id:check.engine_id,environment:check.environment,version:check.version,day_key:day,request_id,status:status.status,incident_code:status.code,observed_at_ms:ms,known_historical_reconcile_excluded:BASELINE};
}
export async function runZeusTick(env,now=Date.now()){
  if(env?.ZEUS_SUPERVISOR_ENABLED!=="true")return {status:"OFF"};
  if(!env?.SUPERVISOR_DB)throw Error("SUPERVISOR_DB_REQUIRED");
  if(!Number.isSafeInteger(now)||now<0)throw Error("INVALID_CLOCK");
  const utcHour=new Date(now).getUTCHours();
  if(utcHour<2)return {status:"BEFORE_P5_DUE",environment:"LAB"};
  const summaries=[];
  for(const check of CHECKS){
    const observation=await observeCheck(env.SUPERVISOR_DB,check,now);
    const id=["ZEUS",check.company_id,check.engine_id,check.environment,check.version,observation.day_key,observation.incident_code].join(":");
    // Additive ZEUS table only; immutable receipt and no update/retry to FACT jobs.
    const write=await env.SUPERVISOR_DB.prepare("INSERT INTO cerebro_zeus_supervisor_events_lab_v1 (event_id,company_id,engine_id,environment,version,check_id,day_key,request_id,status,incident_code,observed_at_ms) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11) ON CONFLICT(event_id) DO NOTHING").bind(id,observation.company_id,observation.engine_id,observation.environment,observation.version,observation.check_id,observation.day_key,observation.request_id,observation.status,observation.incident_code,observation.observed_at_ms).run();
    summaries.push({check_id:check.check_id,status:observation.status,incident_code:observation.incident_code,event_id:id,inserted:Number(write?.meta?.changes||0)});
  }
  return {status:"OBSERVED",environment:"LAB",checks:summaries,external_mutation_allowed:false};
}
export default{
  async fetch(){return new Response(null,{status:404,headers:{"cache-control":"no-store"}});},
  async scheduled(event,env,ctx){
    ctx.waitUntil(runZeusTick(env,event.scheduledTime).then(x=>console.log("ZEUS_SUPERVISOR="+x.status)).catch(()=>console.error("ZEUS_SUPERVISOR=INCIDENT_STORAGE_OR_READ_FAILED")));
  }
};