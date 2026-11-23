# CP77 · ONB-QUEUE claim fencing · LAB ONLY

## Verified risk
In CP75, `OnboardingQueue.complete` and `retry_or_dead_letter` read an item with `get()` and then unconditionally updated it by request_id. Once a lease expired, claimant B could recover the request and increment attempts; claimant A could still write `COMPLETED`, `QUEUED` or `DEAD_LETTER`, overwriting B's decision. Calls against unclaimed/terminal requests were also accepted.

## Fix (no migration)
- Under SQLite `BEGIN IMMEDIATE`, read tenant, status and attempts, enforce active `IN_PROGRESS`, check provided `claim_attempts`, and perform a compare-and-set UPDATE guarded by request_id/status/attempts.
- The existing worker now passes the actual `item.attempts` to both terminal completion and retry.
- `claim_attempts` remains an optional argument for old direct callers; the worker-to-queue path has fencing. Legacy callers without the claim token still require migration before a general multi-worker rollout.
- Ten new tests cover reclaimed leases, old worker completion/retry/dead-letter, unclaimed/terminal protections, concurrent SQLite connection, previous call signature and real worker wiring.
- All tests are synthetic LAB data, no backend changes, no schema changes or remote activations. Separate remote deployment/identity gate still required.

## Safety / rollback
Base CP75 `4f79f3d80229acd080b76e64f4a8d278094d687d`; branch isolated from main. Rollback: revert exactly the CP77 commit or reset its private branch to CP75. Preserve CP75 PR #279 DRAFT, JARVIS Gateway OFF, Brevo 123–126 suspended, UMS-001 publication OFF. GitHub Actions are used only for CI, never as execution runtime.
