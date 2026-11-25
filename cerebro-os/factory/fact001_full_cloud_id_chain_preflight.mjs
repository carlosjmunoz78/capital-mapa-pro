/**
 * FACT-001 V0 full-path preflight. READ-ONLY.
 * Examines already-downloaded Cloudflare LAB worker source strings in memory.
 * A two-worker-only patch MUST NOT be treated as a finished identity migration.
 * No secrets, no network, no Worker deployments and no tenant normalization.
 */
export const OBSERVED_STRICT_WORKERS_V1 = Object.freeze({
  "cerebro-fact001-gateway-lab-eu-20261109": 3,
  "cerebro-fact001-github-oidc-enroll-lab-eu": 1,
  "cerebro-fact001-ums001-issuer-provisioner-lab-eu": 1,
  "cerebro-ums001-registered-image-executor-lab-eu": 1,
  "cerebro-ums001-universal-engine-adapter-lab-eu": 1,
  "cerebro-ums001-universal-gateway-lab-eu": 3,
  "cerebro-ums001-universal-router-lab-eu": 2,
  "cerebro-ums001-universal-runtime-broker-lab-eu": 1,
});

const OLD_ENGINE_RULE = "/^[A-Z][A-Z0-9-]{2,63}$/";
const REQUIRED = Object.keys(OBSERVED_STRICT_WORKERS_V1);

export function auditFactCloudIdChain(sourcesByWorker) {
  if (!sourcesByWorker || typeof sourcesByWorker !== "object" ||
      Array.isArray(sourcesByWorker) ||
      Object.keys(sourcesByWorker).length !== REQUIRED.length ||
      Object.keys(sourcesByWorker).some(k => !REQUIRED.includes(k))) {
    throw new Error("FACT_CHAIN_SCOPE_OR_SOURCE_MISSING");
  }
  const sites = [];
  for (const worker of REQUIRED) {
    const source = sourcesByWorker[worker];
    if (typeof source !== "string" || source.length < 100 || source.length > 200_000) {
      throw new Error("FACT_CHAIN_SOURCE_INVALID");
    }
    const count = source.split(OLD_ENGINE_RULE).length - 1;
    if (count !== OBSERVED_STRICT_WORKERS_V1[worker]) {
      throw new Error("FACT_CHAIN_VALIDATOR_DRIFT:" + worker);
    }
    sites.push(Object.freeze({worker, strict_validator_sites: count}));
  }
  return Object.freeze({
    status: "SOURCE_CONTRACT_AUDITED_NOT_DEPLOYABLE",
    company_id: "fenix",
    environment: "LAB",
    worker_count: REQUIRED.length,
    strict_validator_sites: sites.reduce((sum, row) => sum + row.strict_validator_sites, 0),
    workers: Object.freeze(sites),
    canonical_digit_leading_compatible: false,
    live_worker_patch_deployed: false,
    safe_to_promote: false,
    signed_runtime_enrollment_proven_without_github_actions: false,
    partial_two_worker_update_forbidden: true,
    identified_runtime_id_policy_must_remain_separate: true,
  });
}

/** Require identity alignment; a legal name is not proof of a company_id alias. */
export function auditCompanyScope(companyRegistryId, runtimeRecordId) {
  if (typeof companyRegistryId !== "string" || typeof runtimeRecordId !== "string" ||
      companyRegistryId.length < 2 || runtimeRecordId.length < 2 ||
      !/^[a-z][a-z0-9-]{1,62}$/.test(companyRegistryId) ||
      !/^[a-z][a-z0-9-]{1,62}$/.test(runtimeRecordId)) {
    throw new Error("FACT_COMPANY_SCOPE_INVALID");
  }
  const matched = companyRegistryId === runtimeRecordId;
  return Object.freeze({
    registry_company_id: companyRegistryId,
    runtime_company_id: runtimeRecordId,
    status: matched ? "SAME_CANONICAL_COMPANY_ID" : "HOLD_COMPANY_ID_MISMATCH",
    cross_company_action_allowed: false,
    aliases_automatically_assumed: false,
    facts_can_be_observed_readonly: true,
    attribution_to_registry_allowed: matched,
    needs_explicit_verified_alias_contract: !matched,
  });
}

// CP141: classified real LAB source anchors. Source-only candidate, never deploys.
export const CANONICAL_ENGINE_RULE_CP141 = '/^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/';
const [FACT,BRIDGE,PROVISIONER,EXECUTOR,ADAPTER,GATEWAY,ROUTER,BROKER] = REQUIRED;
const ISSUER_BINDING = 'issuer.origin_engine_id!==e.issuer||issuer.origin_engine_id!==r.origin_engine_id';
const SPEC_CP141 = Object.freeze({
  [FACT]: {inline:['engineId',"engineId||''"], preserveRuntime:true},
  [BRIDGE]: {named:'rxEngine',args:['engine',"body.engine_id||''","body.engine_id||''","input.engine_id||''"]},
  [PROVISIONER]: {named:'id',args:["e.engine_id||''","msg.engine_id||''","input.engine_id||''","input.engine_id||''","payload.engine_id||''","engine_id||''","input.engine_id||''","engine_id||''"]},
  [EXECUTOR]: {named:'engineRx',args:["r.origin_engine_id||''"]},
  [ADAPTER]: {named:'id',args:["r.origin_engine_id||''","r.consumer_engine_id||''","r.origin_engine_id","e.issuer||''"],issuerBinding:true},
  [GATEWAY]: {named:'id',args:["r.origin_engine_id||''","r.consumer_engine_id||''","r.origin_engine_id","e.issuer||''"],issuerBinding:true,inline:["i.origin_engine_id||''","r.origin_engine_id||''"]},
  [ROUTER]: {inline:["r.origin_engine_id||''","r.consumer_engine_id||''"]},
  [BROKER]: {named:'ID',args:["principal.engine_id||''"]}
});
function exactCount(source, text, n, worker) {
  if (source.split(text).length-1!==n) throw Error('FACT_CHAIN_ANCHOR_DRIFT:'+worker);
}
export function planClassifiedCloudIdChainMigration(sourcesByWorker) {
  auditFactCloudIdChain(sourcesByWorker);
  const candidates={}, workers=[];
  for (const worker of REQUIRED) {
    const source=sourcesByWorker[worker], spec=SPEC_CP141[worker], changes=[];
    if (source.includes(CANONICAL_ENGINE_RULE_CP141)) throw Error('FACT_CHAIN_PREEXISTING_CANDIDATE:'+worker);
    if (spec.issuerBinding) exactCount(source,ISSUER_BINDING,1,worker);
    if (spec.preserveRuntime) exactCount(source,OLD_ENGINE_RULE+'.test(runtimeId)',1,worker);
    if (spec.named) {
      const pattern=new RegExp('\\b'+spec.named+'\\.test\\(([^)\\n]{1,130})\\)','g');
      const actual=[...source.matchAll(pattern)].map(m=>m[1]).sort();
      if (JSON.stringify(actual)!==JSON.stringify([...spec.args].sort())) throw Error('FACT_CHAIN_VALIDATOR_USAGE_DRIFT:'+worker);
      if (new RegExp('\\b'+spec.named+'\\.exec\\(').test(source)) throw Error('FACT_CHAIN_UNCLASSIFIED_USAGE:'+worker);
      changes.push(['const '+spec.named+'='+OLD_ENGINE_RULE,'const '+spec.named+'='+CANONICAL_ENGINE_RULE_CP141]);
    }
    for(const arg of spec.inline??[]) changes.push([OLD_ENGINE_RULE+'.test('+arg+')',CANONICAL_ENGINE_RULE_CP141+'.test('+arg+')']);
    let candidate=source;
    for(const [old,next] of changes){exactCount(source,old,1,worker);candidate=candidate.replace(old,()=>next);}
    exactCount(candidate,OLD_ENGINE_RULE,spec.preserveRuntime?1:0,worker);
    exactCount(candidate,CANONICAL_ENGINE_RULE_CP141,changes.length,worker);
    if(spec.issuerBinding)exactCount(candidate,ISSUER_BINDING,1,worker);
    if(spec.preserveRuntime)exactCount(candidate,OLD_ENGINE_RULE+'.test(runtimeId)',1,worker);
    let restored=candidate;
    for(const [old,next] of [...changes].reverse())restored=restored.replace(next,()=>old);
    if(restored!==source)throw Error('FACT_CHAIN_ROUNDTRIP_FAILED:'+worker);
    candidates[worker]=candidate;
    workers.push(Object.freeze({worker,engine_validator_sites_changed:changes.length,runtime_validator_sites_preserved:spec.preserveRuntime?1:0,issuer_origin_binding_preserved:!!spec.issuerBinding,exact_roundtrip:true}));
  }
  const changed=workers.reduce((n,w)=>n+w.engine_validator_sites_changed,0);
  if(changed!==12)throw Error('FACT_CHAIN_SITE_TOTAL_INVALID');
  return Object.freeze({status:'SOURCE_ONLY_CANDIDATE_NOT_DEPLOYED',workers:Object.freeze(workers),engine_validator_sites_changed:changed,runtime_validator_sites_preserved:1,source_candidates:Object.freeze(candidates),safe_to_promote:false,deploy_authorized:false,requires_real_signed_enrollment:true,requires_backup_and_rollback:true});
}

// CP153/154: exact source-only patch of the verified LAB Gateway, no deployment.
export async function planUmsGatewayTenantBoundaryCP153(modules) {
  const old = 'const target=(env,company)=>{const ns=env.MEDIA_LEDGER.jurisdiction(\'eu\');';
  const next = 'const target=(env,company)=>{if(company!==\'fenix\')throw Error(\'UMS001_COMPANY_SCOPE_DENIED\');const ns=env.MEDIA_LEDGER.jurisdiction(\'eu\');';
  if (!modules || typeof modules !== 'object' || Array.isArray(modules) ||
      Object.keys(modules).sort().join('|') !== 'core.mjs|worker.mjs' ||
      Object.values(modules).some(v => typeof v !== 'string' || v.length > 200000)) {
    throw Error('CP153_GATEWAY_MODULE_SCOPE');
  }
  const hash = async s => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))).map(b=>b.toString(16).padStart(2,'0')).join('');
  const worker = modules['worker.mjs'], core = modules['core.mjs'];
  if (await hash(worker) !== 'f4e191d39a6059ec8c27cd385a4d976049da93f482b1dba93fbc8350264fbd41' ||
      await hash(core) !== 'fcbf3a65278abf020653967003324bcdae6b3777e2f556f6297c227622935227' ||
      worker.split(old).length !== 2 || worker.includes(next)) {
    throw Error('CP153_GATEWAY_SOURCE_DRIFT');
  }
  const candidate = worker.replace(old,()=>next);
  if (candidate.replace(next,()=>old) !== worker ||
      await hash(candidate) !== 'd03790272ff45cc220ad55fe57a1d99c8c7388b90a6b83f312ac2f3bf6978dd0') {
    throw Error('CP153_GATEWAY_CANDIDATE_DRIFT');
  }
  return Object.freeze({status:'SOURCE_ONLY_CANDIDATE_NOT_DEPLOYED',company_id:'fenix',environment:'LAB',
    modules:Object.freeze({'worker.mjs':candidate,'core.mjs':core}),exact_roundtrip:true,
    deployment_authorized:false,real_iam_proven:false,safe_to_promote:false});
}
