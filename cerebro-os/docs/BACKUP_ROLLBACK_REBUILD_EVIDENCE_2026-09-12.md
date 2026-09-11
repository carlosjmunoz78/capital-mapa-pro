# CEREBRO OS · Backup / Rollback / Rebuild evidence · 2026-09-12

## Scope
Evidence-first audit of the existing App/CEREBRO recovery contracts. No production mutation, no App PREPROD reactivation, no destructive restore test.

## HECHO / evidenced
- App repository contains `cerebro/docs/AUTONOMY_BACKUP_REBUILD.md` with the recovery contract: Git/pinned source snapshots for App/CEREBRO, Notion inventory snapshots before schema mutation, and non-destructive verification rules.
- App repository contains `.github/workflows/prod-rollback-rehearsal.yml` as a manual `workflow_dispatch` validation gate. It checks current `main`, requires an expected current HEAD, validates the target ref/build/production contracts, and does not mutate `main` or deploy the rollback automatically.
- `cerebro/docs/RUNBOOK.md` defines the emergency rollback sequence as rehearsal → rollback branch → revert commit(s) → PR/gates → merge → exact-SHA PROD deploy/smoke → user-visible verification.
- App rebuild smoke contract exists: `cd cerebro && npm test && npm run validate && npm run generate -- --out ./.cerebro-generated`.
- Existing `EVIDENCE.json` correctly scopes historical exact-SHA PROD deploy/runtime-smoke evidence and explicitly keeps `autonomous_prod=false` for the recorded CEREBRO structural/reference milestones.

## PARCIAL / not proven
- No evidence was found in the retrieved recent manual-dispatch Actions history that `PROD Rollback Rehearsal` has actually been executed. Therefore the workflow **exists**, but rollback rehearsal must not be claimed as tested from this evidence.
- Current Supabase connector surface does not expose a provider backup/restore operation. A provider-level database restore drill is therefore not evidenced here.
- `pg_net` destructive removal/reinstall is not covered by a proven provider restore path and remains blocked from execution.
- Git/source rebuild is not equivalent to database/provider restore. These recovery dimensions remain separate.

## Gate before claiming rollback/restore GREEN
1. Capture an immutable/pinned recovery target and the exact current HEAD.
2. Execute `PROD Rollback Rehearsal` against a known-good target and capture the successful run ID/evidence.
3. Demonstrate the rollback branch/revert procedure without rewriting history.
4. Verify exact-SHA deploy/runtime smoke for the rollback result if/when a real rollback is required.
5. Obtain a provider-supported Supabase backup/restore path or equivalent reproducible database backup and perform a restore drill outside PROD.
6. Record restore duration, integrity checks and rollback/reinstall procedure for extension-adjacent state such as `pg_net`.
7. Update Registry/runbook/evidence only after the proof exists.

## State
- Source/build rebuild contract: **EXISTENTE / VERIFIED BY SOURCE**.
- Rollback workflow definition: **EXISTENTE / VERIFIED BY SOURCE**.
- Rollback rehearsal execution: **POR_AUDITAR / NO EVIDENCE FOUND IN RETRIEVED HISTORY**.
- Provider database restore drill: **BLOCKED BY CURRENT CONNECTOR CAPABILITY / NOT PROVEN**.
- `pg_net` destructive migration/removal: **PARCIAL_CONTROLLED / DO NOT EXECUTE**.

## Rule
Never convert the presence of a workflow or runbook into proof that recovery was successfully rehearsed. Recovery is GREEN only after execution evidence exists.
