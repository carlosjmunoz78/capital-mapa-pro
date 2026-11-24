# CEREBRO FORGE PREPROD deployment notes

The GitHub Workload Identity provider is scoped to repository `carlosjmunoz78/capital-mapa-pro` and branch `cerebro-engine-factory-v0`.

The deployment workflow verifies the configured project ID and both dedicated service accounts after successful WIF authentication. It intentionally does not call `gcloud projects describe`, because that read requires the Cloud Resource Manager API, which is not needed for the PREPROD runtime itself and is not enabled in the zero-cost bootstrap.

## 2026-11-23 · FORGE no-traffic acceptance gate — HOLD

**Observed, not inferred:** Cloud Run candidate `cerebro-advisory-preprod-00266-xnc` has 0% traffic and **0 Cloud Logging startup records**; the previous `00264-dpv` serves 100%. See GitHub Actions read-only run [45238014743](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/45238014743). Image OCI child verification and isolation already pass; do not re-run image investigations.

**Missing channel:** In project `cerebro-forge`, Cloud Tasks / Cloud Scheduler APIs are disabled and no Cloud Run Job or other service is registered in `europe-southwest1`; see read-only run [45238384614](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/45238384614). A GitHub-hosted runner cannot reach this private `ingress=internal` service from outside the VPC, even using an IAM token.

**Cost/runtime guard:** FORGE `deploy-preprod` is now **skipped before allocating a runner** unless the *repository-level* GitHub configuration variable `CEREBRO_FORGE_INTERNAL_CANARY_READY` is exactly `true`. The variable was not created or enabled during this checkpoint; PR [#293](https://github.com/carlosjmunoz78/capital-mapa-pro/pull/293). This gate prevents repeated Docker builds, Artifact Registry pushes, and unusable 0%-traffic revisions. Skipped is **HOLD**, not successful deployment or promotion.

**Acceptance to re-enable:** First establish an existing or approved, cost-measured, authenticated *same-project* invoker that can request the exact **tagged, private candidate** without moving service traffic. Verify request, true startup logs, remote-onboarding evidence, three-type observability coverage, strict IAM and preserved 100% previous revision, and rollback. Only then set the repo-level variable, run the original workflow, and promote to PREPROD after all gates. Do not enable new paid services, reduce ingress security, relax verification or touch App/CRM/PROD. Do not set `CEREBRO_FORGE_INTERNAL_CANARY_READY` based solely on a local container rehearsal.

## 2026-11-24 — Accepted existing revision, automatic pipeline candidate

Physical PREPROD 00266-xnc accepted by internal OIDC Cloud Tasks HTTP 200, 111/111 synthetic observability pairs and real traffic rollback; now 100% serving. Existing dedicated queue forge-private-canary-20261124 is PAUSED, one attempt, one concurrent dispatch and one per second. The patch keeps the repository readiness guard OFF. Before enabling it, grant only dedicated queue permissions (get/pause/resume/create/list/delete tasks) to existing WIF deployer and actAs only on the dedicated invoker SA; verify via the new read-only preflight job on the trusted canonical branch. No project-wide queue admin or keys. Future runs tag exact candidate, create one named task while paused, resume, verify correlated task and Cloud Run logs, pause and remove the temporary tag before the old acceptance gates. No automatic retry or new queue. Cost headroom must remain verified. Rollback this patch on its own; do not rollback accepted serving revision unless required.
