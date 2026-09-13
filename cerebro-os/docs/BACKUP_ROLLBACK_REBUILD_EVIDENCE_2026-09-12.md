# CEREBRO OS · Backup / Rollback / Rebuild evidence · 2026-09-14

## Scope
Evidence-first audit of App/CEREBRO recovery contracts. No production mutation, no destructive restore test, no paid Supabase preview branch created.

## HECHO / evidenced
- Immutable Git source snapshot is proven on branch `cerebro-engine-factory-v0`.
- Current Factory CI proves deterministic rebuild/runtime rehearsal on the active branch.
- `cerebro-os/runtime/recovery_external_evidence_inventory.py` separates source backup, rebuild/runtime rehearsal and provider restore instead of treating them as equivalent.
- `cerebro-os/runtime/recovery_zero_cost_strategy.py` keeps the default recovery path at 0 EUR additional recurring cost and blocks PROD database restore/destructive tests.
- `cerebro-os/runtime/zero_cost_recovery_rehearsal.py` now performs a real isolated local/CI backup → restore rehearsal using a SHA-256 manifest, restores into a second isolated path, checks byte-level integrity, runs post-restore smoke validation and removes the temporary recovery workspace.
- `cerebro-os/tests/test_zero_cost_recovery_rehearsal.py` proves empty-source and traversal inputs fail closed, and verifies backup integrity, restore integrity, JSON smoke, cleanup, no secrets, no PROD mutation and 0 EUR additional cost.
- Factory CI run `34788667726`, job `verify`, completed **SUCCESS** and executed the full unit-test suite plus the existing runtime/release rollback rehearsals.

## CORRECTION OF PREVIOUS SNAPSHOT
A previous evidence note stated that `.github/workflows/prod-rollback-rehearsal.yml` existed in the repository. A live read of `.github/workflows` on `cerebro-engine-factory-v0` showed only `cerebro-engine-factory-v0.yml`. Therefore the previous workflow-existence statement is stale and must not be used as current evidence.

This correction does not remove any existing production behavior. It only corrects the evidence classification.

## PARCIAL / not proven
- The new isolated restore rehearsal is **LOCAL/CI**, not a provider-level Supabase database restore.
- A dedicated PROD rollback workflow is **not present in the current audited branch**.
- Runtime/release rollback rehearsal is proven in CI, but a real PROD release rollback execution is not proven.
- Provider-level Supabase database restore drill is not proven.
- No paid Supabase Preview Branch has been created; paid fallback remains subject to `MONEY_LIMIT`.
- Git/source/local-CI restore is not equivalent to database/provider restore.
- `pg_net` destructive removal/reinstall remains blocked until provider restore evidence and rollback are proven.

## Zero-cost order of operations
1. Preserve immutable Git snapshot evidence.
2. Use deterministic CI rebuild/runtime rollback rehearsal.
3. Rehearse backup/restore/integrity/smoke/cleanup locally or in CI with no provider cost.
4. Prefer an existing non-PROD provider resource only where technically equivalent and safely isolated.
5. Use provider-native temporary restore only when it can be demonstrated safely and without PROD mutation.
6. Treat any paid branch/project as a fallback requiring `MONEY_LIMIT` confirmation.
7. Never claim provider restore from source, CI or filesystem evidence.

## Gate before claiming recovery GREEN
1. Source backup reference exists and is immutable. **HECHO**.
2. Rebuild evidence is successful. **HECHO**.
3. Isolated local/CI restore integrity, post-restore smoke and cleanup succeed. **HECHO**.
4. Real release/PROD rollback target is demonstrated outside destructive PROD execution. **PENDIENTE**.
5. Provider-supported database restore is demonstrated outside PROD. **PENDIENTE**.
6. Provider restore integrity/smoke checks succeed. **PENDIENTE**.
7. Provider restore cleanup/retention is evidenced. **PENDIENTE**.

## State
- Source snapshot: **HECHO / PROVEN**.
- Rebuild/runtime rehearsal: **HECHO / GREEN_CODE_CI**.
- Zero-cost isolated local/CI restore: **HECHO / GREEN_CI**.
- Backup integrity SHA-256: **HECHO / GREEN_CI**.
- Post-restore smoke: **HECHO / GREEN_CI**.
- Recovery cleanup: **HECHO / GREEN_CI**.
- Factory evidence run: **34788667726 / SUCCESS**.
- PROD release rollback target/execution: **PARCIAL / NOT PROVEN**.
- Provider database restore drill: **PARCIAL / NOT PROVEN**.
- Paid Supabase branch: **NOT CREATED**.
- Additional recurring cost introduced by this recovery strategy: **0 EUR**.
- `pg_net` destructive migration/removal: **PARCIAL_CONTROLLED / DO NOT EXECUTE**.

## Rule
Never convert documentation, source rebuild or local/CI restore rehearsal into proof of provider restore or real PROD rollback. Recovery becomes globally GREEN only after the corresponding provider/release execution evidence exists.
