# CP87 · ZEUS → SUP-001 / GOV-001 native read model

Status: **CANDIDATE LAB** until active Cloudflare cron processes a real CP86 receipt. Same cron/runtime `cerebro-fact001-recovery-runner-lab`, D1 `cerebro-fact001-recovery-lab-eu`; no GPT automation or additional Worker.

Upstream source: immutable CP86 `zeus_fact_p5_health_v1` receipt `ZEUS-P5-YYYYMMDD-fenix-capital-LAB`, validated tenant, engine, environment, version, day, fingerprint, event state/source. When not present, report `AWAIT_SOURCE` and retry harmlessly on existing cron without creating an incident. Read-only against upstream tables.

Projection: append-only `zeus_fact_p5_registry_projection_v1` holding `LAB_GREEN`/ `BLOCKED`, evidence ref, checksum and `promotion_allowed=0`. This is an **existing Engine Registry / Supervisor contract-compatible scoped LAB projection**, NOT a fully deployed global GOV-001 registry. Do not change canonical engine registry, existing status Python code or PROD.

Exceptions: a `BLOCKED` observation produces deduplicated `zeus_fact_p5_exceptions_v1` record. Strict project exception codes only: `AUTOMATION_DRIFT`→`POLICY_CONFLICT`, `DAILY_JOB_MISSING_OR_SCOPE_INVALID`→`LOW_CONFIDENCE`, `RECEIPT_OR_COST_INVALID`→`HIGH_RISK`, `NEW_RECONCILE`→`LOW_CONFIDENCE`. `DAILY_JOB_NOT_COMPLETED` remains ordinary supervisor review (no automatic human escalation). An incident is a persistent internal signal, not an email, public route, publication or automatic provider call. Human exception flag is **not** a human notification; resolution workflow to be built later. Never retry unknown external effects or deactivate a subsystem automatically.

Security and cost: exact scope `fenix-capital / FACT-001 / LAB / 1.0.0`, no extra resources, no additional cron. Feature flag `ZEUS_P5_ROUTER_ENABLED` defaults OFF, separate from existing `ZEUS_P5_MONITOR_ENABLED`. No external network calls, no new IAM. No secrets in exceptions. Additional fee not authorized; query D1 totals and Cloudflare free-plan resource limits before promotion.

Rollback: current proven CP86 Worker v11 `776a1e70-616f-42c9-a7e4-3400063d9e7c` remains one-click deployment rollback target; previous CP86 monitor OFF v10 `73c84caf-f79d-47da-b33d-6c2938029495`. Additive D1 tables retained as audit, not dropped. Snapshot D1 Time Travel bookmark, and ensure old wrapper is byte-identical except new import and waitUntil. Promotion to PROD forbidden until full gate.
