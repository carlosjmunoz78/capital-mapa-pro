# CEREBRO OS · Make → Runtime migration progress · 2026-09-12

## Purpose
Evidence-first register for deterministic logic being moved out of Make into CEREBRO runtime. OLD Make scenarios are preserved until dependency and parity gates allow retirement. No active Make route is disabled merely because replacement code exists.

## Inventory baseline
- Make CORE inventory/classification: **62/62 GREEN**.
- Make TEST inventory/classification: **120/120 GREEN**.
- Inventory closure is distinct from runtime migration/promotion.

## GREEN_CODE_CI · 9524837 · Idempotencia y Run ID
OLD Make contract inspected live: `ExistRecord` followed by stable Data Store registration. First occurrence is `FIRST_SEEN`; repeated use of the same stable key becomes `BLOCKED_DUPLICATE`; run IDs are timestamp based; no external connector is involved.

NEW runtime replacement:
- `runtime/idempotency.py`
- SQLite persistence through the existing multi-company runtime store.
- scope: `company_id + engine_id + environment + version + idempotency_key`.
- preserves operation/external identity and run ID semantics.
- duplicate same-scope claims fail closed before downstream action.
- tests: `tests/test_runtime_idempotency.py`.
- CI workflow `34690764066`: `success`.

Status: **GREEN_CODE_CI / OLD preserved / retirement not yet authorized**.

## GREEN_CODE_CI · 9527162 · Logs universales V1
OLD Make contract inspected live: Data Store start/final records share one run ID and persist phase, status, external ID, network, operation, human flag, automatic action, Notion record ID and version. No external connector is involved.

NEW runtime replacement:
- `runtime/execution_log.py`
- canonical start/final execution-log contract persisted in SQLite.
- exact tenant/environment/version isolation.
- same run ID can hold distinct `start` and `final` phases; duplicate phase is blocked.
- validation covers identity, environment, phase and attempt count.
- tests: `tests/test_runtime_execution_log.py`.
- CI workflow `34690818510`: `success`.

Status: **GREEN_CODE_CI / OLD preserved / retirement not yet authorized**.

## GREEN_CODE_CI · 9527140 · Router Maestro V1
OLD Make contract inspected live: Data Store-only route decision `ROUTED_TO_FACEBOOK_ANALYTICS_TEST`, followed by an execution log. The OLD scenario explicitly states that the router does not publish or execute the adapter.

NEW runtime replacement:
- `runtime/router.py`
- deterministic `RouteDecision` contract.
- multi-company/environment/version isolation.
- route-level idempotency.
- hard invariant: router can only emit a decision; attempts to configure an external action are rejected.
- duplicate same-scope route is fail-closed.
- tests: `tests/test_runtime_router.py`.
- CI workflow `34690904190`: `success`.

Status: **GREEN_CODE_CI / OLD preserved / retirement not yet authorized**.

## Promotion/retirement gate
None of the three OLD scenarios is deleted or repurposed yet. To move from `GREEN_CODE_CI` to `REPLACE_AFTER_PARITY/RETIRE`, require:
1. caller/dependency map,
2. representative OLD fixtures or historical evidence,
3. OLD vs NEW output comparison,
4. rollback path,
5. consumer cutover evidence,
6. target-environment evidence.

## Next migration queue
Priority deterministic candidates: `9525004` validation/normalization, `9533976` Story preflight/queue, `9533982` multimedia request, `9535463` ADS router/preflight, `9537817` Notion dispatcher. Active `9527242` reconciliation and active `9555725` Signal→Idea→Evaluación→Laboratorio remain parallel until replacement parity is proven.