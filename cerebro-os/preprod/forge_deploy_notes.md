# CEREBRO FORGE PREPROD deployment notes

The GitHub Workload Identity provider is scoped to repository `carlosjmunoz78/capital-mapa-pro` and branch `cerebro-engine-factory-v0`.

The deployment workflow verifies the configured project ID and both dedicated service accounts after successful WIF authentication. It intentionally does not call `gcloud projects describe`, because that read requires the Cloud Resource Manager API, which is not needed for the PREPROD runtime itself and is not enabled in the zero-cost bootstrap.

## 2026-11-23 · FORGE no-traffic acceptance gate — HOLD

**Observed, not inferred:** Cloud Run candidate `cerebro-advisory-preprod-00266-xnc` has 0% traffic and **0 Cloud Logging startup records**; the previous `00264-dpv` serves 100%. See GitHub Actions read-only run [45238014743](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/45238014743). Image OCI child verification and isolation already pass; do not re-run image investigations.

**Missing channel:** In project `cerebro-forge`, Cloud Tasks / Cloud Scheduler APIs are disabled and no Cloud Run Job or other service is registered in `europe-southwest1`; see read-only run [45238384614](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/45238384614). A GitHub-hosted runner cannot reach this private `ingress=internal` service from outside the VPC, even using an IAM token.

**Cost/runtime guard:** FORGE `deploy-preprod` is now **skipped before allocating a runner** unless the *repository-level* GitHub configuration variable `CEREBRO_FORGE_INTERNAL_CANARY_READY` is exactly `true`. The variable was not created or enabled during this checkpoint; PR [#293](https://github.com/carlosjmunoz78/capital-mapa-pro/pull/293). This gate prevents repeated Docker builds, Artifact Registry pushes, and unusable 0%-traffic revisions. Skipped is **HOLD**, not successful deployment or promotion.

**Acceptance to re-enable:** First establish an existing or approved, cost-measured, authenticated *same-project* invoker that can request the exact **tagged, private candidate** without moving service traffic. Verify request, true startup logs, remote-onboarding evidence, three-type observability coverage, strict IAM and preserved 100% previous revision, and rollback. Only then set the repo-level variable, run the original workflow, and promote to PREPROD after all gates. Do not enable new paid services, reduce ingress security, relax verification or touch App/CRM/PROD. Do not set `CEREBRO_FORGE_INTERNAL_CANARY_READY` based solely on a local container rehearsal.
