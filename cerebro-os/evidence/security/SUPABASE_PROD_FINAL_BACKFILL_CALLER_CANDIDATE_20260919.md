# Supabase PROD · final session-context caller deployment candidate · 2026-09-19

Status: DEFINED / NOT DEPLOYED.

Target Edge Function: `fenix-document-existing-backfill`.

Live source before change:
- version: `7`;
- SHA-256: `049c41052556d38a4860369143aa04e455344067a0b584d46cb728bb75a9ec39`;
- verify_jwt: `true`;
- exact rollback snapshot: `cerebro-os/evidence/security/edge-function-snapshots/fenix-document-existing-backfill-v7.ts`.

Prepared candidate:
- `cerebro-os/evidence/security/deploy-candidates/fenix-document-existing-backfill-v8.ts`.

The only intended authentication change is:
`authenticated user RPC fenix_prod_session_context()`
->
`auth.getUser(bearer) + service-role fenix_prod_actor_context_by_auth_server(p_auth_user_id)`.

Business logic, backfill batching, document routing, existing SQL server wrappers, role checks, terminal-stage checks and write behavior are preserved unchanged.

The current execution channel refused the live deploy of this function under safety controls. Therefore this candidate is NOT evidence of a live deployment.

No SQL ACL retirement is authorized by this file. After deployment, live source must be re-read, authenticated HTTP E2E must be proven, and only then can selective ACL retirement be considered with explicit authorization.
