# CP87 · ZEUS → SUP-001 / GOV-001 native read model

Status: **CANDIDATE LAB** until active Cloudflare cron processes a real CP86 receipt. Same cron/runtime `cerebro-fact001-recovery-runner-lab`, D1 `cerebro-fact001-recovery-lab-eu`; no GPT automation or additional Worker.

Upstream source: immutable CP86 `zeus_fact_p5_health_v1` receipt `ZEUS-P5-YYYYMMDD-fenix-capital-LAB`, validated tenant, engine, environment, version, day, fingerprint, event state/source. When not present, report `AWAIT_SOURCE` and retry harmlessly on existing cron without creating an incident. Read-only against upstream tables.

Projection: append-only `zeus_fact_p5_registry_projection_v1` holding `LAB_GREEN`/ `BLOCKED`, evidence ref, checksum and `promotion_allowed=0`. This is an **existing Engine Registry / Supervisor contract-compatible scoped LAB projection**, NOT a fully deployed global GOV-001 registry. Do not change canonical engine registry, existing status Python code or PROD.

Exceptions: a `BLOCKED` observation produces deduplicated `zeus_fact_p5_exceptions_v1` record. Strict project exception codes only: `AUTOMATION_DRIFT`→`POLICY_CONFLICT`, `DAILY_JOB_MISSING_OR_SCOPE_INVALID`→`LOW_CONFIDENCE`, `RECEIPT_OR_COST_INVALID`→`HIGH_RISK`, `NEW_RECONCILE`→`LOW_CONFIDENCE`. `DAILY_JOB_NOT_COMPLETED` remains ordinary supervisor review (no automatic human escalation). An incident is a persistent internal signal, not an email, public route, publication or automatic provider call. Human exception flag is **not** a human notification; resolution workflow to be built later. Never retry unknown external effects or deactivate a subsystem automatically.

Security and cost: exact scope `fenix-capital / FACT-001 / LAB / 1.0.0`, no extra resources, no additional cron. Feature flag `ZEUS_P5_ROUTER_ENABLED` defaults OFF, separate from existing `ZEUS_P5_MONITOR_ENABLED`. No external network calls, no new IAM. No secrets in exceptions. Additional fee not authorized; query D1 totals and Cloudflare free-plan resource limits before promotion.

Rollback: current proven CP86 Worker v11 `776a1e70-616f-42c9-a7e4-3400063d9e7c` remains one-click deployment rollback target; previous CP86 monitor OFF v10 `73c84caf-f79d-47da-b33d-6c2938029495`. Additive D1 tables retained as audit, not dropped. Snapshot D1 Time Travel bookmark, and ensure old wrapper is byte-identical except new import and waitUntil. Promotion to PROD forbidden until full gate.

## Remote execution log · 2026-11-23 (LAB only)

- Verified CP86 active Worker version `776a1e70-616f-42c9-a7e4-3400063d9e7c`, plus one persisted real receipt `ZEUS-P5-20261123-fenix-capital-LAB` GREEN.
- Created **only two additive D1 tables** in the existing recovery D1: `zeus_fact_p5_registry_projection_v1` and `zeus_fact_p5_exceptions_v1`; zero alterations to original P5 tables. D1 Time Travel bookmark was verified; NEVER restore the whole DB just to rollback the Worker.
- Candidate Worker v12 `107694b7-50f9-4b11-b872-28dae27817ff` was deployed briefly with ZEUS router OFF. A subsequent version upload failed Cloudflare compile validation (HTTP 400, Worker parse error). Rolled back promptly and verified **v11 active again**, preserving all P5 data. No evidence that v12 produced a failed scheduled invocation; root cause of compile error not independently proven.
- Reconstructed candidate directly from trusted GitHub module sources and legacy modules; Cloudflare accepted version v13 `d267fa63-312a-4ac7-8c37-56c2640b5544`, `ZEUS_P5_ROUTER_ENABLED=true`, `ZEUS_P5_MONITOR_ENABLED=true`, `P5_ENABLED=true`.
- Physically deployed v13 100% to the existing `cerebro-fact001-recovery-runner-lab` Worker, deployment `18589406-0714-4416-b2c7-497c055e0c82`; same `*/5 * * * *` cron and no public route. **At the time of writing, the first new registry projection is PENDING a normal cron invocation**, not yet an acknowledged live E2E receipt. Do not claim the registry router operational until D1 readback confirms.
- Rollback target: deploy previously validated v11 `776a1e70-616f-42c9-a7e4-3400063d9e7c` with 100% traffic, leaving D1 additive audit tables retained. Never route these LAB status rows as PROD proof.
- CI run `45152810742`: 1439 tests per suite, 0 failures, 2/14 skipped; both new CP87 tests passed on Linux. The latter test suite had no Node interpreter for the JS test.
