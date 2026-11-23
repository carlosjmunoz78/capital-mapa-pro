# CP75 · Onboarding Context Loader Scope Guard (LAB only)

## Evidence and reason
CP74 protects incoming `context_id` and exact idempotent replays, but the optional `context_loader` could subsequently overwrite the validated `console_context_ref` with `company:aion` while `company_id=fenix`. That allowed a new queued payload to carry a cross-company context without having to replay a request. The source path and expected behavior were verified against the existing CP74 branch before changing code.

## Change
The loader's returned `company_id` remains governed as before. When the loader returns `console_context_ref`, it must be a nonempty string, it must not resolve to another company, and when the incoming request supplied a context ID, the loaded reference must match that ID. Metadata-only loaders and matching company loaders retain their existing behavior. No SQLite schema, IAM scopes, cron, deployments, protected branches or production systems are changed.

## Tests / acceptance
New `test_onboarding_loader_scope_cp75.py` includes 9 checks for cross-company refs, ref swaps, empty/nonstring refs, compatible same-company and metadata-only loaders, preexisting tenant checks, idempotent replay, and no-write rejection. Existing CP74 and console dispatch tests are deliberately kept unchanged for regression. CI/remote execution must be verified separately before promoting this branch; source readback alone does not count as a PASS. IAM identity attestation and signed execution receipts are still pending.

## Rebuild / rollback
Base CP74: `db779d42fc29fab32efd96022426a8bc344bc26c`. Rebuild by restoring CP74. Roll back CP75 by resetting the dedicated LAB branch to its exact parent or reverting the isolated commit; keep old CP74 untouched. No PROD deployment.
