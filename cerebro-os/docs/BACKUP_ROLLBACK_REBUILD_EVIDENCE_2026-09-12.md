# CEREBRO OS · Backup / Rollback / Rebuild evidence · 2026-09-13

## Scope
Evidence-first audit of App/CEREBRO recovery contracts. No production mutation, no destructive restore test, no paid Supabase preview branch created.

## HECHO / evidenced
- Immutable Git source snapshot is proven by commit `e0e5b41e3a05198d015af7bcd0387d4ff3c66e48` on branch `cerebro-engine-factory-v0`.
- Current Factory CI proves deterministic rebuild/runtime rehearsal on the active branch.
- `cerebro-os/runtime/recovery_external_evidence_inventory.py` separates source backup, rebuild/runtime rehearsal and provider restore instead of treating them as equivalent.
- `cerebro-os/runtime/recovery_zero_cost_strategy.py` keeps the default recovery path at 0 EUR additional recurring cost and blocks PROD database restore/destructive tests.

## CORRECTION OF PREVIOUS SNAPSHOT
A previous evidence note stated that `.github/workflows/prod-rollback-rehearsal.yml` existed in the repository. A live read of `.github/workflows` on `cerebro-engine-factory-v0` on 2026-09-13 shows only `cerebro-engine-factory-v0.yml`. Therefore the previous workflow-existence statement is stale and must not be used as current evidence.

This correction does not remove any existing production behavior. It only corrects the evidence classification.

## PARCIAL / not proven
- A dedicated PROD rollback workflow is **not present in the current audited branch**.
- Runtime rollback rehearsal is proven in CI, but a real PROD release rollback rehearsal is not proven.
- Provider-level Supabase database restore drill is not proven.
- No paid Supabase Preview Branch has been created; paid fallback remains subject to `MONEY_LIMIT` and explicit confirmation.
- Git/source rebuild is not equivalent to database/provider restore.
- `pg_net` destructive removal/reinstall remains blocked until provider restore evidence and rollback are proven.

## Zero-cost order of operations
1. Preserve immutable Git snapshot evidence.
2. Use deterministic CI rebuild/runtime rollback rehearsal.
3. Prefer existing non-PROD resources for isolated validation where technically equivalent.
4. Use provider-native temporary restore only when it can be demonstrated safely and without PROD mutation.
5. Treat any paid branch/project as a fallback requiring `MONEY_LIMIT` confirmation.
6. Never claim provider restore from source or CI evidence.

## Gate before claiming recovery GREEN
1. Source backup reference exists and is immutable.
2. Rebuild evidence is successful.
3. Release/PROD rollback rehearsal is executed and captured, not merely documented.
4. Provider-supported database restore is demonstrated outside PROD.
5. Integrity/smoke checks succeed after restore.
6. Cleanup/retention is documented.
7. Registry/runbook/evidence are updated only after proof exists.

## State
- Source snapshot: **HECHO / PROVEN**.
- Rebuild/runtime rehearsal: **HECHO / GREEN_CODE_CI**.
- Dedicated PROD rollback workflow on current branch: **NOT PRESENT / PREVIOUS SNAPSHOT STALE**.
- PROD release rollback rehearsal execution: **POR_AUDITAR / NOT PROVEN**.
- Provider database restore drill: **EXTERNAL_PROOF_PENDING / NOT PROVEN**.
- Paid Supabase branch: **NOT CREATED**.
- Additional recurring cost introduced by this recovery strategy: **0 EUR**.
- `pg_net` destructive migration/removal: **PARCIAL_CONTROLLED / DO NOT EXECUTE**.

## Rule
Never convert documentation, source rebuild or runtime rehearsal into proof of provider restore or real PROD rollback. Recovery becomes GREEN only after the corresponding execution evidence exists.
