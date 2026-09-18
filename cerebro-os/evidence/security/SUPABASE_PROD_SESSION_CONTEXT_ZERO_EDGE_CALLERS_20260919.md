# Supabase PROD · session_context Edge caller closure · 2026-09-19

Status: READY_FOR_SELECTIVE_ACL_RETIREMENT_AUTHORIZATION · NOT YET AUTHORIZED.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Live final caller deployment

`fenix-document-existing-backfill` has been deployed successfully as:

- version: `8`;
- status: `ACTIVE`;
- verify_jwt: `true`;
- live SHA-256: `cfe78207a52d5edaab2a02c1938394d55cd8e28aeef0c1acea2edcfc907de810`;
- direct `rpc('fenix_prod_session_context')` / `rpc("fenix_prod_session_context")`: ABSENT;
- `fenix_prod_actor_context_by_auth_server`: PRESENT;
- bearer identity validation through `auth.getUser`: PRESENT.

Rollback source is preserved at:

`cerebro-os/evidence/security/edge-function-snapshots/fenix-document-existing-backfill-v7.ts`

Deployment candidate source is preserved at:

`cerebro-os/evidence/security/deploy-candidates/fenix-document-existing-backfill-v8.ts`

## ACTIVE Edge inventory disposition

Immediately before this final deployment, all 42 ACTIVE Edge Functions were source-inspected for an exact direct call to `fenix_prod_session_context()`. The only remaining exact caller was `fenix-document-existing-backfill` v7.

After deployment, the ACTIVE inventory still contains 42 functions and the previously inspected versions remain unchanged apart from the intended backfill update to v8. The live v8 source has been re-read and the direct legacy call is absent.

Therefore the known ACTIVE Edge Function direct-caller count for `fenix_prod_session_context()` is now:

`0`

This statement applies to the inspected ACTIVE Supabase Edge Function inventory. It does not by itself prove absence of every possible external REST/RPC client outside that inventory.

## Current Security Advisor

The live Security Advisor still reports 16 `authenticated_security_definer_function_executable` findings because the ACL on `fenix_prod_session_context()` has intentionally NOT been revoked yet.

Other current advisor findings remain:
- 46 `rls_enabled_no_policy` INFO;
- 1 `extension_in_public` WARN for `pg_net`;
- 1 `auth_leaked_password_protection` WARN.

No bulk remediation is authorized by this evidence.

## Next gate

Selective retirement of `authenticated EXECUTE` on exactly:

`public.fenix_prod_session_context()`

requires fresh explicit HIGH_RISK authorization before applying DDL.

Required authorization phrase:

`AUTORIZO RETIRO SELECTIVO RPC PROD`

No other function privilege, RLS policy, extension, Auth setting, App/CRM data, or Edge Function is included in that authorization.

## Rollback requirement

Before applying the revoke, capture live ACL/definition evidence and prepare the inverse grant. After applying, re-run:
1. privilege verification;
2. Security Advisor;
3. Edge caller source verification;
4. supported authenticated-path E2E if a valid test identity/token is available.

If any required path fails, rollback immediately using the preserved inverse grant and re-verify.

## Promotion statement

This closure does NOT declare global SECURITY green, global autonomy, or PROD promotion. It closes only the known Supabase Edge direct-caller dependency on `fenix_prod_session_context()`.


## Live ACL / definition snapshot before any retirement

Read-only PostgreSQL verification captured immediately after the v8 caller closure:

- schema: `public`;
- function: `fenix_prod_session_context()`;
- `SECURITY DEFINER`: `true`;
- `authenticated EXECUTE`: `true`;
- `anon EXECUTE`: `false`;
- `service_role EXECUTE`: `true`;
- function definition MD5: `42fc119c18a2c7d8e500bd9bee1bb90c`.

This is the pre-retirement fingerprint. No privilege was changed by this verification.
