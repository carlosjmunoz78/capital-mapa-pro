// CP87. ZEUS -> SUP-001 / GOV-001 native LAB read model.
// Only consumes a previously persisted CP86 receipt; never changes FACT jobs.
const SCOPE=Object.freeze({company_id:'fenix-capital',engine_id:'FACT-001',environment:'LAB',version:'1.0.0'});
const ALLOWED=new Set(['GREEN','AUTOMATION_DRIFT','DAILY_JOB_MISSING_OR_SCOPE_INVALID','DAILY_JOB_NOT_COMPLETED','RECEIPT_OR_COST_INVALID','NEW_RECONCILE']);
const EXCEPTION_POLICY=Object.freeze({
 AUTOMATION_DRIFT:'POLICY_CONFLICT',
 DAILY_JOB_MISSING_OR_SCOPE_INVALID:'LOW_CONFIDENCE',
 RECEIPT_OR_COST_INVALID:'HIGH_RISK',
 NEW_RECONCILE:'LOW_CONFIDENCE'
});
function dayUTC(ms){return new Date(ms).toISOString().slice(0,10).replace(/-/g,'');}
export function normalizeZeusP5Receipt(receipt,dayKey) {
 const id='ZEUS-P5-'+dayKey+'-fenix-capital-LAB',request='FACT001-P5-'+dayKey;
 if(!receipt||receipt.receipt_id!==id||receipt.day_key!==dayKey||
    receipt.request_id!==request||receipt.company_id!==SCOPE.company_id||
    receipt.engine_id!==SCOPE.engine_id||receipt.environment!==SCOPE.environment||
    receipt.version!==SCOPE.version||receipt.source!=='ZEUS_P5_SHARED_RUNTIME'||
    typeof receipt.fingerprint_sha256!=='string'||!(/^[0-9a-f]{64}$/.test(receipt.fingerprint_sha256))||
    !ALLOWED.has(receipt.code)||receipt.state!==(receipt.code==='GREEN'?'GREEN':'BLOCKED')||
    !Number.isSafeInteger(Number(receipt.observed_at_ms))||Number(receipt.observed_at_ms)<=0)
    throw new Error('ZEUS_P5_UNTRUSTED_OBSERVATION');
 const human=EXCEPTION_POLICY[receipt.code]??null;
 return Object.freeze({
  snapshot_id:'GOV-001:FACT-001:P5:LAB:'+dayKey,
  receipt_id:id,request_id:request,day_key:dayKey,
  ...SCOPE, registry_state:receipt.state==='GREEN'?'LAB_GREEN':'BLOCKED',
  health_code:receipt.code,
  exception_class:human,
  human_required:human!==null,
  supervisor_action:receipt.state==='GREEN'?'NONE':'SUPERVISOR_REVIEW',
  source_sha256:receipt.fingerprint_sha256,
  promotion_allowed:false,external_mutation_allowed:false
 });
}
export async function ingestZeusP5Supervisor(env,scheduledTime=Date.now()){
 if(env?.ZEUS_P5_ROUTER_ENABLED!=='true'||!env.RECOVERY_DB)return {status:'OFF'};
 if(!Number.isSafeInteger(scheduledTime)||scheduledTime<=0)throw new Error('ZEUS_P5_INVALID_TIME');
 const day=new Date(scheduledTime);
 if(day.getUTCHours()<2)return {status:'NOT_DUE'};
 const dayKey=dayUTC(scheduledTime),sourceId='ZEUS-P5-'+dayKey+'-fenix-capital-LAB';
 const db=env.RECOVERY_DB;
 const source=await db.prepare(
   'SELECT receipt_id,company_id,engine_id,environment,version,day_key,request_id,state,code,observed_at_ms,fingerprint_sha256,source FROM zeus_fact_p5_health_v1 WHERE receipt_id=?1'
 ).bind(sourceId).first();
 if(!source)return {status:'AWAIT_SOURCE',receipt_id:sourceId};
 const status=normalizeZeusP5Receipt(source,dayKey);
 await db.prepare(
   'INSERT INTO zeus_fact_p5_registry_projection_v1 (snapshot_id,company_id,engine_id,environment,version,day_key,receipt_id,request_id,registry_state,health_code,supervisor_action,source_sha256,created_at_ms,promotion_allowed) '+
   'VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,0) ON CONFLICT(snapshot_id) DO NOTHING'
 ).bind(status.snapshot_id,status.company_id,status.engine_id,status.environment,status.version,status.day_key,status.receipt_id,
        status.request_id,status.registry_state,status.health_code,status.supervisor_action,status.source_sha256,scheduledTime).run();
 const saved=await db.prepare(
   'SELECT registry_state,health_code,receipt_id,source_sha256,promotion_allowed FROM zeus_fact_p5_registry_projection_v1 WHERE snapshot_id=?1'
 ).bind(status.snapshot_id).first();
 if(!saved||saved.registry_state!==status.registry_state||saved.health_code!==status.health_code||
    saved.receipt_id!==status.receipt_id||saved.source_sha256!==status.source_sha256||
    Number(saved.promotion_allowed)!==0)throw new Error('ZEUS_P5_REGISTRY_CONFLICT');
 let incidentId=null;
 if(status.registry_state==='BLOCKED'){
   incidentId='SUP-001:FACT-001:P5:LAB:'+dayKey+':'+status.health_code;
   await db.prepare(
     'INSERT INTO zeus_fact_p5_exceptions_v1 (incident_id,snapshot_id,company_id,engine_id,environment,version,day_key,code,exception_class,human_required,source_sha256,created_at_ms,incident_state) '+
     "VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,'OPEN') ON CONFLICT(incident_id) DO NOTHING"
   ).bind(incidentId,status.snapshot_id,status.company_id,status.engine_id,status.environment,status.version,
          status.day_key,status.health_code,status.exception_class,status.human_required?1:0,status.source_sha256,scheduledTime).run();
   const incident=await db.prepare(
     'SELECT code,exception_class,human_required,source_sha256,incident_state FROM zeus_fact_p5_exceptions_v1 WHERE incident_id=?1'
   ).bind(incidentId).first();
   if(!incident||incident.code!==status.health_code||
      (incident.exception_class??null)!==status.exception_class||
      Number(incident.human_required)!==(status.human_required?1:0)||
      incident.source_sha256!==status.source_sha256||incident.incident_state!=='OPEN')
      throw new Error('ZEUS_P5_EXCEPTION_CONFLICT');
 }
 return {status:'SYNCED',day_key:dayKey,snapshot_id:status.snapshot_id,
         registry_state:status.registry_state,health_code:status.health_code,
         incident_id:incidentId,human_required:status.human_required,
         promotion_allowed:false,external_mutation_allowed:false};
}
