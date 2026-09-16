# Supabase PROD · authenticated SECURITY DEFINER caller map · 2026-09-16

Status: PARCIAL · live evidence updated after selective caller migrations. SECURITY global remains fail-closed.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Scope

This evidence tracks selective retirement of the 16 remaining `SECURITY DEFINER` functions executable by `authenticated`. No bulk revoke is authorized. Retirement requires caller coverage, parity, authenticated HTTP E2E and rollback evidence.

## Live Edge Function evidence

### `fenix-app-gateway` v18

The live gateway authenticates the bearer token, resolves identity server-side through `fenix_prod_actor_context_by_auth_server`, and invokes service-role-only `*_server` wrappers. Its inspected source contains no direct call to the 16 legacy authenticated SECDEF names.

### `fenix-profile-api` v2

The live profile API validates bearer identity server-side and uses `fenix_prod_profile_get_full_server`, `fenix_prod_profile_update_full_server` and `fenix_prod_profile_goals_get_server`. No direct call to the four legacy profile `_user` functions was present in the inspected source.

### `fenix-b2b-actions` v10 · MIGRATED IN PROD

The former direct authenticated call to `fenix_prod_session_context()` was removed. Live PROD v10 now uses:

- bearer token;
- `auth.getUser()` with the publishable/anon client;
- service-role `fenix_prod_actor_context_by_auth_server(p_auth_user_id)`;
- the existing B2B role and scope checks unchanged in intent.

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

### Additional inspected Edge Functions

The following live authenticated surfaces already use server-side identity rather than legacy `fenix_prod_session_context()`:

- `fenix-directory-actions` v8;
- `fenix-task-actions` v1;
- `fenix-expediente-actions` v1.

These inspections materially reduce caller uncertainty but do not prove absence of every external REST/RPC caller or every deployed client.

## Current selective disposition

- `fenix_prod_session_context`: `MIGRATED_KNOWN_EDGE_CALLERS_ACL_RETIREMENT_STILL_BLOCKED`.
- The two previously proven live Edge callers are migrated and live-source verified.
- `authenticated HTTP E2E` for the migrated B2B and Ana paths remains `POR_AUDITAR`; no authenticated test token was available in this execution path.
- Exhaustive absence of additional external/direct RPC callers remains `POR_AUDITAR`.
- Therefore `authenticated EXECUTE` on `fenix_prod_session_context()` MUST NOT be revoked yet.
- Profile legacy functions remain candidates for selective retirement only after equivalent caller coverage + E2E.
- Chat/contact/inmo legacy functions remain `CANDIDATE_OR_KEEP_BY_CONTRACT` pending exact per-function caller disposition.
- No bulk revoke and no mass conversion to `SECURITY INVOKER`.

## Latest Supabase Advisor after both migrations

The migrations changed callers, not the function ACL, so the Advisor correctly still reports 16 `authenticated_security_definer_function_executable` findings. Other current findings remain:

- 46 `rls_enabled_no_policy` INFO findings;
- 1 `extension_in_public` WARN for `pg_net`;
- 1 `auth_leaked_password_protection` WARN.

The earlier anon-SECDEF and mutable-search-path issues have not reappeared in the current advisor response.

## Promotion / safety statement

These migrations do not grant SECURITY green, global autonomy, PROD promotion or permission to revoke legacy ACLs automatically. App/CRM data, tables, RLS policies and business records were not rewritten by these caller migrations. Rollback source exists for both changed Edge Functions.
