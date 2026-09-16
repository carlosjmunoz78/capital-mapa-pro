# Supabase PROD · session context caller migration · fenix-ana-api · 2026-09-16

Status: HECHO para migración estructural del caller; ACL retirement global sigue BLOQUEADO.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Before

`fenix-ana-api` PROD v10 was ACTIVE with SHA-256 `a58b60cae208d9d499090dc0aae795e1a005fc0cecc54993b7e4df1803634434` and resolved identity through direct authenticated `fenix_prod_session_context()`.

Rollback source is preserved at:

`cerebro-os/evidence/security/edge-function-snapshots/fenix-ana-api-v10.ts`

## Change

The function now validates the bearer with `auth.getUser()` and resolves actor identity through service-role `fenix_prod_actor_context_by_auth_server(p_auth_user_id)`. Existing capabilities/corrections/decision routes and Notion synchronization logic were otherwise preserved in intent.

## Live deployment proof

- function: `fenix-ana-api`;
- status: `ACTIVE`;
- version: `11`;
- SHA-256: `b657f7336fb7baac4fce236f2158c778ccd896a742c87d378ece44c744ce0cc5`;
- `verify_jwt=true` preserved.

## Remaining blockers

Known direct callers still requiring migration:

- `fenix-memory-api` v9;
- `fenix-evidence-api` v13.

`authenticated EXECUTE` on `fenix_prod_session_context()` MUST NOT be revoked yet. Authenticated HTTP E2E and exhaustive external/direct REST/RPC caller absence also remain `POR_AUDITAR`.

No SQL ACL/function body, RLS policy, App/CRM record, business data or promotion flag was modified by this deployment. This evidence does not grant SECURITY green.