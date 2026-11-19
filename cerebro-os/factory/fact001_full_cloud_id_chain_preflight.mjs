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
