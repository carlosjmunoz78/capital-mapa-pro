# Supabase PROD · authenticated SECURITY DEFINER caller map · 2026-09-16

Status: PARCIAL · live evidence expanded after selective caller migrations. SECURITY global remains fail-closed.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Scope

This evidence tracks selective retirement of the 16 remaining `SECURITY DEFINER` functions executable by `authenticated`. No bulk revoke is authorized. Retirement requires caller coverage, parity, authenticated HTTP E2E and rollback evidence.

## Live Edge Function evidence

### `fenix-app-gateway` v18

The live gateway authenticates the bearer token, resolves identity server-side through `fenix_prod_actor_context_by_auth_server`, and invokes service-role-only `*_server` wrappers. Its inspected source contains no direct call to the 16 legacy authenticated SECDEF names.

### `fenix-profile-api` v2

The live profile API validates bearer identity server-side and uses `fenix_prod_profile_get_full_server`, `fenix_prod_profile_update_full_server` and `fenix_prod_profile_goals_get_server`. No direct call to the four legacy profile `_user` functions was present in the inspected source.

### `fenix-b2b-actions` v10 · MIGRATED IN PROD

The former direct authenticated call to `fenix_prod_session_context()` was removed. Live PROD v10 now uses bearer validation, `auth.getUser()` and service-role `fenix_prod_actor_context_by_auth_server(p_auth_user_id)` while preserving the existing B2B role/scope checks in intent.

Deployment verification:

- status: `ACTIVE`;
- version: `10`;
- SHA-256: `057dc41b86de5a3dcc059f58249dde16424e1b19937ead891f2bfebf5e610884`;
- rollback source preserved at `cerebro-os/evidence/security/edge-function-snapshots/fenix-b2b-actions-v9.ts`.

### `fenix-ana-knowledge` v10 · MIGRATED IN PROD

The former direct authenticated call to `fenix_prod_session_context()` was removed. Live PROD v10 now uses bearer validation, `auth.getUser()` and service-role `fenix_prod_actor_context_by_auth_server(p_auth_user_id)` while preserving the existing knowledge/review flow in intent.

Deployment verification:

- status: `ACTIVE`;
- version: `10`;
- SHA-256: `970beb8876a3ad657124fc28038cb040a42d3fa8ffd9f2ee2bcc07ce6ec66ce2`;
- rollback source preserved at `cerebro-os/evidence/security/edge-function-snapshots/fenix-ana-knowledge-v9.ts`.

## Newly discovered live callers during exhaustive expansion

The earlier two-caller inventory was incomplete. Direct inspection of additional ACTIVE Edge Functions discovered four more live authenticated callers of `fenix_prod_session_context()`:

- `fenix-ana-canonical` v9, hash `17c953d8a3641ca0a22a77884e889d82ec938e775d259d07df5708803c041e59`;
- `fenix-memory-api` v9, hash `1769a05a99bc4fd1b6da9b4d852d3117e8de090d1322757290c60064571eeda8`;
- `fenix-evidence-api` v13, hash `71ead424adebbf4e3c162fc897f1a105ba414ca9950577c66dec312771ba6d21`;
- `fenix-ana-api` v10, hash `a58b60cae208d9d499090dc0aae795e1a005fc0cecc54993b7e4df1803634434`.

All four validate a bearer token and then call the legacy authenticated RPC directly through a user client before applying their existing domain authorization. They therefore block retirement of `authenticated EXECUTE` on `fenix_prod_session_context()` until each surface is migrated and validated.

### Additional inspected surfaces already on server-side identity

The following inspected ACTIVE Edge Functions already use bearer -> `auth.getUser()` -> service-role `fenix_prod_actor_context_by_auth_server` and do not directly call legacy `fenix_prod_session_context()`:

- `fenix-directory-actions` v8;
- `fenix-task-actions` v1;
- `fenix-expediente-actions` v1;
- `fenix-directory-api` v9;
- `fenix-economia-api` v8;
- `fenix-task-api` v12;
- `fenix-bank-api` v8;
- `fenix-reports-api` v8.

The ACTIVE Edge Function inventory contains additional functions that still require source-level caller disposition before absence can be treated as proven.

## Database-side dependency search

A read-only `pg_proc` search over ordinary functions for definitions containing `fenix_prod_session_context` returned only:

- `public.fenix_prod_session_context()` itself;
- `public.fenix_prod_session_context_server(p_actor_code text)`.

No additional ordinary PostgreSQL function body was identified as a database-side caller in that search. This does not prove absence of external REST/RPC clients.

## Current selective disposition

- `fenix_prod_session_context`: `RETIREMENT_BLOCKED_ADDITIONAL_LIVE_CALLERS_DISCOVERED`.
- Two formerly known Edge callers are migrated and live-source verified.
- Four additional ACTIVE Edge callers remain to migrate: `fenix-ana-canonical`, `fenix-memory-api`, `fenix-evidence-api`, `fenix-ana-api`.
- `authenticated HTTP E2E` for migrated and pending replacement paths remains `POR_AUDITAR` where a usable authenticated test token is not available in the current execution path.
- Exhaustive source inspection of the remaining ACTIVE Edge Function inventory remains `POR_AUDITAR`.
- External/direct REST/RPC caller absence remains `POR_AUDITAR`.
- Therefore `authenticated EXECUTE` on `fenix_prod_session_context()` MUST NOT be revoked yet.
- Profile legacy functions remain candidates for selective retirement only after equivalent caller coverage + E2E.
- Chat/contact/inmo legacy functions remain `CANDIDATE_OR_KEEP_BY_CONTRACT` pending exact per-function caller disposition.
- No bulk revoke and no mass conversion to `SECURITY INVOKER`.

## Latest Supabase Advisor

The caller migrations do not change the function ACL, so the Advisor correctly still reports 16 `authenticated_security_definer_function_executable` findings. Other current findings remain:

- 46 `rls_enabled_no_policy` INFO findings;
- 1 `extension_in_public` WARN for `pg_net`;
- 1 `auth_leaked_password_protection` WARN.

The earlier anon-SECDEF and mutable-search-path issues have not reappeared in the current advisor response.

## Promotion / safety statement

These caller migrations and audits do not grant SECURITY green, global autonomy, PROD promotion or permission to revoke legacy ACLs automatically. App/CRM data, tables, RLS policies and business records were not rewritten by this caller-audit step.


## Addendum 2026-09-18 · final ACTIVE Edge caller sweep

The closure sweep expanded source inspection to 42 ACTIVE Edge Functions and found seven additional direct `fenix_prod_session_context()` callers beyond the earlier inventory.

Live migrations completed in this sweep:
- `fenix-memory-api` v10;
- `fenix-evidence-api` v14;
- `fenix-document-intelligence-test` v9;
- `fenix-document-intelligence` v13;
- `fenix-document-extract` v13;
- `fenix-communications-gateway` v9;
- `fenix-document-reread` v3;
- `fenix-document-auto-ingest` v3.

Current exact direct legacy caller remaining in the ACTIVE inventory:
- `fenix-document-existing-backfill` v7.

The full evidence, versions, hashes, rollback anchors and fail-closed disposition are recorded in:
`cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_FINAL_CALLER_CLOSURE_20260918.md`.

ACL retirement remains blocked until the backfill caller is migrated and authenticated HTTP E2E is proven.
