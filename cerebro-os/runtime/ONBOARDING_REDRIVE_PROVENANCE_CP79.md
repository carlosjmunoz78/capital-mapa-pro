# CP79 · Provenance preservation for redrive (LAB)

## Why
CP78 fixed the atomic state transition but intentionally preserved the historical payload replacement behavior. A partial redrive payload could erase `source` (`CEREBRO_CONSOLE.user_id/request_id`) and validated `context.console_context_ref`. An attacker requeueing a WAITING case could also provide new source evidence with another user. Downstream permission enforcement must never infer identity from a redrive payload.

## Modification
Within CP78's existing BEGIN IMMEDIATE transaction: preserve original source and context when omitted; reject source changes or source injection into legacy records without provenance; forbid changes to authenticated context reference (including within same company) while permitting metadata updates. Keep company/version/environment and status fencing from CP78. Zero schema changes, no PROD/data mutation or new subscription.

## Tests / limitations
11 new synthetic tests: missing source/context restoration, metadata merge, different user/request source injection, null source, context-ref swaps, cross-tenant swaps, persistence across SQLite reopen and legacy no-source rejection. Existing CP78/CP77 tests remain unchanged. Does not prove IAM authorization (identity provenance is not an authentication proof). Legacy callers omitting `claim_attempts` remain compatibility-only until separately migrated.

## Rollback
Base CP78 `f3ddca6c40b0a2d36f67f16d276b77d629d1e618`. Revert CP79 commit or reset isolated LAB branch to CP78 after evidence snapshot; do not merge main, deploy, activate JARVIS Gateway or alter Brevo/UMS.
