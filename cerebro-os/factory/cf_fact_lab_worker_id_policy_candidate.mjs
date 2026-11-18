/**
 * FACT-001 LAB contract repair candidate for two ALREADY DEPLOYED Cloudflare workers.
 * Pure transform; no API, deployment, secret reads, feature toggle or network.
 * Never apply until inventory+snapshot+tests+PREPROD+rollback gates are green.
 */
export const CANONICAL_ENGINE_ID_RE = /^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/;

const ALLOWED = Object.freeze({
  'cerebro-fact001-github-oidc-enroll-lab-eu': {
    old: 'const rxEngine=/^[A-Z][A-Z0-9-]{2,63}$/;',
    next: 'const rxEngine=/^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/;',
  },
  'cerebro-fact001-ums001-issuer-provisioner-lab-eu': {
    old: 'const id=/^[A-Z][A-Z0-9-]{2,63}$/;',
    next: 'const id=/^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/;',
  },
});

export function patchFactLabWorkerIdPolicy(workerName, originalSource) {
  const rule = ALLOWED[workerName];
  if (!rule || typeof originalSource !== 'string' ||
      originalSource.length < 100 || originalSource.length > 180_000) {
    throw new Error('FACT_LAB_SOURCE_OR_WORKER_DENIED');
  }
  if (!originalSource.includes('FACT001_ENGINE_CREATED') ||
      (workerName.includes('issuer-provisioner') && !originalSource.includes('FACT_EVENT_SIGNATURE_DENIED')) ||
      (workerName.includes('github-oidc') && !originalSource.includes('OIDC_BRIDGE_ENABLED'))) {
    throw new Error('FACT_LAB_SOURCE_NOT_VERIFIED');
  }
  if (originalSource.split(rule.old).length !== 2 || originalSource.includes(rule.next)) {
    throw new Error('FACT_LAB_ID_POLICY_ANCHOR_DRIFT');
  }
  // Exactly one text substitution; preserves all authentication, signing,
  // flags, bindings, queues, routes, replay guards and paid-usage constraints.
  const updatedSource = originalSource.replace(rule.old, rule.next);
  if (updatedSource.length - originalSource.length !== rule.next.length - rule.old.length) {
    throw new Error('FACT_LAB_UNEXPECTED_CHANGE');
  }
  return Object.freeze({
    worker_name: workerName,
    old_policy: rule.old,
    new_policy: rule.next,
    source: updatedSource,
    deploy_authorized: false,
    owner_production_unchanged: true,
    requires_signed_runtime_identity: true,
    cloudflare_customer_cost_measured: false,
    needs_postdeployment_real_signature_ack: true,
  });
}

export function isCanonicalEngineId(value) {
  return typeof value === 'string' && CANONICAL_ENGINE_ID_RE.test(value);
}
