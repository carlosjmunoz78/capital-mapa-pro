# CEREBRO OS · CP69 · CE-17 / Onboarding SQLite connection lifecycle

## Scope
Fix only `cerebro-os/runtime/onboarding_queue.py` in an isolated LAB branch. No migration, schema or queue API changes. No network, production, App, CRM, marketing sends or new paid resources.

## Failure verified on OLD
`with sqlite3.Connection() as conn` commits or rolls back the transaction, but does **not** close the database connection. Original `OnboardingQueue` used this 10 times, leaving SQLite handles open. `claim()` already used an explicit try/finally/close and is preserved.

- OLD added closure regression: `test_all_read_write_connections_are_closed` FAIL, `test_connection_closes_on_sqlite_error` FAIL.
- NEW uses `_managed_connection()` with a contextmanager around the original transaction semantics and an unconditional `conn.close()` in `finally`.
- NEW: **24/24 Python tests PASS**, covering 3 new connection tests, 14 existing console runtime and persistent-store tests and 7 other HTTP boundary tests (from the repository). Original persistence, retry/dead-letter, multiempresa filtering and recovery remain available.
- NEW replays the same queue database after reopening and verifies `fenix` versus `aion` isolation and retry state.
- Some unrelated `ResourceWarning` messages still originate from the existing ConsoleStore, which also uses `with self._connect()`; CP69 is not a global fix for every SQLite connection.

## Safety and rollback
No queries or indexes changed. No deletion or new table. Restore original file by reverting the CP69 commit and compare the tree to its exact parent. Verify record counts and `company_id` after any environment-specific integration.

## Promotion gates
Gateway remains OFF; do not promote to production without isolated runtime acceptance, backups/rebuild, policy, durable audit and costs. This LAB patch is not CE-11 remote Node acceptance.