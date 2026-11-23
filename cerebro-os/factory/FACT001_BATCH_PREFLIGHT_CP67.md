# CEREBRO OS · FACT-001 · CP67 · Batch scaffold guard

## Scope
Existing repository: `carlosjmunoz78/capital-mapa-pro`, base branch `cerebro-engine-factory-v0` (existing implementation). Changes are limited to:

- `cerebro-os/factory/factory.py`: align engine ID acceptance with the existing UMS-001 enrollment contract (`^[A-Z][A-Z0-9-]{2,63}$`); malformed IDs fail before filesystem writes.
- `cerebro-os/factory/mass_scaffold.py`: canonical duplicate preflight, existing destination checks, single-writer exclusive filesystem lock, rejection of symlinked batch root, fail-closed on fully credentialed remote enrollment, local partial-scaffold rollback only for paths created in the current batch.
- `cerebro-os/tests/test_mass_scaffold_cp67.py`: regression and rollback tests.

## Old vs new and proof
Reproduced on existing code using isolated `TemporaryDirectory`:

- OLD `generate_all(root,['AAA-111','../BAD'])`: errors on second ID **after** `AAA-111` exists.
- OLD `generate_all(root,['aaa-111','AAA-111'])`: duplicates after canonicalization; first engine exists and next call fails.
- NEW rejects both batches in preflight before any engine directory is created.
- NEW with a synthetic hook failing after creating its own second destination removes both new engine folders, leaves previously present `KEEP-01` unchanged, and releases its own lock.
- NEW rejects pre-existing lock **without removing it**; rejects fully configured remote queue dispatch to avoid treating in-process filesystem rollback as a cancellation of a network event.
- NEW successfully scaffolds two real engines and preserves existing UMS-001 PENDING enrollment behavior when no authorized company/transport was supplied.
- 18/18 tests, including 3/3 pre-existing `test_factory.py` tests and 4/4 existing `test_factory_universal_media_enrollment.py` tests, passed in an isolated temporary Python source workspace.

## Safety caveat
This is **local batch consistency**, not an ACID transaction across external systems and not a distributed lock for other components. A remote enrollment dispatched before rollback cannot be undone; this batch path fails closed when a complete remote transport configuration is present. An abandoned lock after a process crash must only be released manually after confirming that no batch is running. No automatic stale-lock stealing. No force-overwrite of existing engine directories. No promotion or deploy.

## Rollback
Keep original Git commit as immutable base. On LAB branch, `git revert <CP67 commit>` and compare the resulting tree with the exact parent tree. No remote rollback or production changes are authorized by this packet. Verify no new files or modified engine outputs remain before promotion.

## Next gates
Review existing callers of `MassScaffoldPlan.output_paths` (its output now reflects canonical uppercase IDs); full integration tests on a disposable checkout; identity-scoped remote job acceptance remains a separate CE-11 gate. Keep `CEREBRO Gateway` OFF.