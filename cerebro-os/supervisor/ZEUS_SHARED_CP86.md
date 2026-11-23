# CP86 · ZEUS shared supervisor · LAB canary

## Exact target
- company_id: fenix-capital
- engine_id: FACT-001
- environment: LAB
- version: 1.0.0
- check_id: FACT001_P5_DAILY_READ_V1
- runtime: ONE shared ZEUS Cloudflare Worker, extensible check registry (not per-engine)
- storage: existing FACT LAB D1 `cerebro-fact001-recovery-lab-eu`
- jobs: read-only SELECT against fact001_p5_jobs_v1 + fact001_p5_automation_registry_v1
- effects: append-only to NEW isolated table cerebro_zeus_supervisor_events_lab_v1
- scheduled: once every 15 minutes AFTER code/rollback gates, skip daily check before 02:00 UTC
- network: no outgoing HTTP; public fetch always 404; workers.dev/preview must be disabled
- cost: no subscription/new D1/API-model use; enforce account Workers Free and current quota
- policy: no new HUMAN_REQUIRED, requeue, automation changes or external notification
- historical exception baseline: FACT001-P5-20261112 (attempts=0), excluded from *new incident* count

## Acceptance / isolation
Source checked into LAB branch only. Need CI green, additive migration, D1 Time Travel bookmark, current resource identity check, test canary cron/durable write, confirm idempotency and code rollback. Do not alter P5 runner/operator crons or their live code. No worker-per-motor: new ZEUS is reusable shared supervisor, future engine checks use same runtime.

## Rollback
Pause/delete only newly created ZEUS LAB Worker and its cron. Leave additive table inert (do NOT restore entire existing FACT LAB D1 or DROP any existing table). If retention removal is later approved, drop only this new table and its index after external backup. Existing FACT jobs are never updated. Do not automatically resolve or retry historic RECONCILE. Production promotion remains NO_GO.
