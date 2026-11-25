// CP162: candidate-only FACT inventory data port. No HTTP route, grants or deployment.
export const FACT_CANDIDATE_SQL = "SELECT engine_id, version, state, artifact_count FROM fact001_factory_candidates_lab_v1 WHERE company_id = ? AND environment = ? AND state = 'CANDIDATE_REGISTERED' AND authority_verified = 0 AND execution_granted = 0 AND production_authorized = 0 AND media_dispatch_enabled = 0 AND cost_ceiling_eur = 0 ORDER BY engine_id, version LIMIT 200";
const scope = Object.freeze({company_id:'fenix',engine_id:'FACT-001',environment:'LAB',capability:'FACT.INVENTORY.READ',read_only:true,external_mutation_allowed:false,cost_ceiling_eur:0});
const fields = [...Object.keys(scope),'request_id','version','principal_id','policy_receipt_ref','emitted_at_epoch'];
const exact=(o,k)=>o && typeof o==='object' && !Array.isArray(o) && Object.keys(o).sort().join('|')===[...k].sort().join('|');
const validId=x=>typeof x==='string' && /^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const validRef=x=>typeof x==='string' && /^[A-Za-z0-9_.:/-]{8,200}$/.test(x);
const deny=code=>{throw new Error(code)};
// Both ports MUST be bound by the trusted runtime; no caller-provided grant or boolean.
export function createFactoryCandidateReader({db,authenticateJarvis,readCurrentGrant,principalId,issuerId,clock=()=>Math.floor(Date.now()/1000)}={}){
  if(!db || typeof db.prepare!=='function' || typeof authenticateJarvis!=='function' || typeof readCurrentGrant!=='function' || !validId(principalId) || !validId(issuerId) || principalId===issuerId || typeof clock!=='function')deny('CP162_TRUSTED_PORTS_REQUIRED');
  return async function read(request,proof){
    const now=clock();
    if(!Number.isSafeInteger(now)|| !exact(request,fields)||Object.entries(scope).some(([k,v])=>request[k]!==v)||!validId(request.request_id)||!validRef(request.policy_receipt_ref)||request.principal_id!==principalId||typeof request.version!=='string'||!/^\d+\.\d+\.\d+$/.test(request.version)||!Number.isSafeInteger(request.emitted_at_epoch)||request.emitted_at_epoch>now||now-request.emitted_at_epoch>60)deny('CP162_REQUEST_SCOPE_DENIED');
    const verifiedRequest=Object.freeze({...request});
    if(await authenticateJarvis(verifiedRequest,proof)!==true)deny('CP162_CALLER_DENIED');
    const g=await readCurrentGrant(verifiedRequest.policy_receipt_ref);
    if(!g||Object.entries({...scope,issuer_id:issuerId,principal_id:principalId,request_id:verifiedRequest.request_id,version:verifiedRequest.version,policy_receipt_ref:verifiedRequest.policy_receipt_ref,decision:'ALLOW_READ_ONLY',verified:true,active:true,revoked:false}).some(([k,v])=>g[k]!==v))deny('CP162_GRANT_SCOPE_DENIED');
    const t=clock(), start=g.issued_at_epoch,end=g.expires_at_epoch,checked=g.checked_at_epoch;
    if(![t,start,end,checked].every(Number.isSafeInteger)||!(0<=start&&start<=checked&&checked<=t&&t<end&&end-start<=900&&t-checked<=60&&start<=verifiedRequest.emitted_at_epoch&&verifiedRequest.emitted_at_epoch<end))deny('CP162_GRANT_FRESHNESS_DENIED');
    const result=await db.prepare(FACT_CANDIDATE_SQL).bind('fenix','LAB').all();
    if(result?.success!==true||!Array.isArray(result.results)||result.results.length>200)deny('CP162_STORAGE_DENIED');
    const entries=result.results.map(r=>{
      if(!exact(r,['engine_id','version','state','artifact_count'])||typeof r.engine_id!=='string'||!/^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/.test(r.engine_id)||typeof r.version!=='string'||!/^\d+\.\d+\.\d+$/.test(r.version)||r.state!=='CANDIDATE_REGISTERED'||!Number.isSafeInteger(r.artifact_count)||r.artifact_count<1)deny('CP162_STORAGE_SCOPE_DENIED');
      return Object.freeze({...r});
    });
    return Object.freeze({status:'CANDIDATE_INVENTORY_READ',request_id:verifiedRequest.request_id,company_id:'fenix',environment:'LAB',engine_id:'FACT-001',entries:Object.freeze(entries),count:entries.length,operational_instances_certified:false,external_mutation_allowed:false,promotion_allowed:false,receipt_persisted:false});
  };
}
