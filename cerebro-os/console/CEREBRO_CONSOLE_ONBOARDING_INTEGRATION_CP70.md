# CEREBRO OS · CP70 · JARVIS Console + Onboarding · Integrated LAB candidate

## Exact parents and scope
- Proposed LAB parent: `carlosjmunoz78/capital-mapa-pro` at CP68 commit `64d7e7113ab89f811af1b5b76c17783100a7d771` (not main).
- Reuses and preserves CP68 audit-secret guard and its durable-before-memory audit.
- Integrates the distinct CP69 SQLite queue lifecycle fix into the same LAB branch.
- Fixes the remaining ConsoleStore SQLite connection leak (5 with-context sections). `sqlite3.Connection.__exit__` commits but does not close.
- New regression for ConsoleStore and CP69 OnboardingQueue. Zero new libraries, workers, cron, API or paid services.

## Old vs new
- Original short-lived ConsoleStore connections were left open after context managers, even on errors. Candidate uses a small `_managed_connection` context manager with `try: with conn: yield conn / finally: conn.close()`.
- `claim()` in the OnboardingQueue retains its existing explicit transaction and manual close.
- Confirmed on synthetic dual-company DB: reader isolation (`fenix` vs `aion`), retry, restart, secret rejection, same-scope idempotency and scope conflict.
- Full co-located Python suite **32/32 PASS** with `PYTHONWARNINGS=error::ResourceWarning` (no leaked handles detected in this exercised path).
- **No changes** to production authentication, the request_id replay contract, schema, Gateway configuration or routes. Production not deployed.

## Limits and rollback
- The durable audit path is **not atomically coupled** to a remote engine enqueue; an external queued side effect cannot be undone by SQLite rollback. The Console/Gateway must remain OFF until the E2E tribunal and relevant identity gates pass.
- The exclusivity of the audit `request_id` remains the existing first-write semantics. A strict contradictory payload mode is a separate contractual decision, not silently changed here.
- Rollback: revert this CP70 commit on the isolated LAB branch and compare the result with CP68 parent tree. Do not merge to main or enable external actions.

## Next acceptance
Authorized private runtime and principal, persistent SQLite acceptance under concurrent operations, backup/restore, cross-tenant negative tests, actual audit receipt and cost measured 0€; CE-11 Node execution remains blocked separately.