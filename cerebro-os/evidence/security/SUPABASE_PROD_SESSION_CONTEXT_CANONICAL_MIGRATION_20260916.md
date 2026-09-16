# Supabase PROD · session context caller migration · fenix-ana-canonical · 2026-09-16

Status: HECHO para migración estructural del caller; ACL retirement global sigue BLOQUEADO.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Before

`fenix-ana-canonical` PROD v9 was ACTIVE with SHA-256 `17c953d8a3641ca0a22a77884e889d82ec938e775d259d07df5708803c041e59` and called `fenix_prod_session_context()` directly through the authenticated user client.

Rollback source is preserved at:

`cerebro-os/evidence/security/edge-function-snapshots/fenix-ana-canonical-v9.ts`

## Change

The caller was migrated without changing its business route or Notion canonical-read flow:

1. require bearer token as before;
2. validate token with `auth.getUser()` using the anon/publishable client;
3. resolve actor identity server-side through service-role `fenix_prod_actor_context_by_auth_server(p_auth_user_id)`;
4. preserve existing `/rules` domain filter and response contract.

No SQL function body, ACL, table, RLS policy, App/CRM record, Notion record or promotion flag was changed by this deployment.

## Live deployment proof

- Edge Function: `fenix-ana-canonical`;
- status: `ACTIVE`;
- version: `10`;
- SHA-256: `dc9c251a248c0151efbfe87f3a53b072c6650ea97592e5825c493d6ea999d5da`;
- `verify_jwt=true` preserved.

## Remaining retirement blockers

`authenticated EXECUTE` on `fenix_prod_session_context()` MUST NOT be revoked yet. At least these known live callers still remain on the legacy RPC and require the same snapshot -> migrate -> verify sequence:

- `fenix-memory-api` v9;
- `fenix-evidence-api` v13;
- `fenix-ana-api` v10.

Authenticated HTTP E2E and exhaustive external/direct REST/RPC caller absence also remain `POR_AUDITAR`.

This evidence does not grant SECURITY green, autonomous PROD promotion or blanket permission to revoke legacy ACLs.