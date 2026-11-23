# CEREBRO OS · JARVIS CONSOLE · CP68 · fail-closed audit metadata

## Existing source and safe scope
- Repository: `carlosjmunoz78/capital-mapa-pro`, from existing `cerebro/techscout-private-gateway-lab-20261121`.
- Changes: `cerebro-os/console/persistent_store.py`, `cerebro-os/console/runtime_builder.py`, and one new test file `cerebro-os/tests/test_console_audit_fail_closed_cp68.py`.
- No network calls, new tenants, Gateway activation or production changes. Existing data untouched.

## OLD reproduction
1. The metadata storage filter rejected exact keys `token`, `api_key`, etc., but accepted variants such as nested `access_token`, `clientSecret`, `refresh-token`, persisting synthetic credential strings into SQLite `metadata_json`.
2. `runtime_builder.audit_sink` appended to the in-memory audit list before calling SQLite. On simulated SQLite write error, an in-memory audit appeared even though no durable record existed.

## NEW behavior
- Normalize key aliases (case/underscores/hyphens/camelCase) and deny common secret-bearing fields recursively. Permit reference-only fields such as `secret_ref` and `credential_ref_id`.
- Reject bearer/basic/token credential values in `authorization` fields, while retaining statuses such as `authorization: GRANTED`.
- Store audit in SQLite first, then append to in-memory audit only after confirmed persistence.
- **Preserve legacy contract:** `ConsoleStore.record` still treats same-scope `request_id` replays with different results as immutable historical first-write, without changing the old audit. The old test expressly requires this behavior. Strict payload conflict semantics need a separate, compatibility-gated migration; not claimed by CP68.
- Failures in other transactional components (for example a queue accepted before audit persistence) are not made atomic by this patch. Gateway stays OFF.

## Tests and rollback
- 20/20 local Python unittest cases passed, including 4 existing ConsoleStore tests and 10 existing console runtime tests.
- Negative cases: sensitive aliases/nested fields rejected; synthetic SQLite failure adds no phantom memory receipt; tenant mismatch denied; legacy replay semantics unchanged.
- Existing runtime SQLite connection `ResourceWarning` observed in the original onboarding queue module: out of scope, tracked for separate correction.
- Rollback requires reverting CP68 branch commit after comparing to the exact parent tree. No automatic promotion.

## Next gate
Re-run against actual isolated LAB runtime with authorized identity. Do not promote before separate E2E tests (tenant access, SQLite transactionality with job dispatch, backup/restore, audit trail, cost/rollback).