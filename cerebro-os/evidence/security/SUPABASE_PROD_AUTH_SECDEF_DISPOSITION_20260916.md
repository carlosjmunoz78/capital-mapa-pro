# Supabase PROD · authenticated SECURITY DEFINER disposition · 2026-09-16

Status: HECHO · read-only classification after authorized PROD security remediation.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Current advisor state

After closing the anon exposure and the two mutable `search_path` warnings, Supabase Security Advisor still reports 16 `authenticated_security_definer_function_executable` warnings.

A live catalog/definition audit was run for all 16 surfaces. Current ACL invariant for every row:

- `authenticated EXECUTE = true`
- `anon EXECUTE = false`
- `service_role EXECUTE = true`
- `SECURITY DEFINER = true`

All 16 definitions bind behavior to `auth.uid()` directly. Fifteen also have an explicit identity/scope/role/ownership guard recognizable in the function contract; `fenix_prod_session_context()` is read-only and scopes its only lookup directly to `auth.uid()` and returns `{}` when no active actor matches.

## Read-only / session-scoped surfaces

These are read-only (`STABLE`) and directly bind returned data to the signed-in user/session:

- `fenix_prod_ana_knowledge_answer_user(text)`
- `fenix_prod_chat_conversations_user()`
- `fenix_prod_chat_list_v2_user(text, integer)`
- `fenix_prod_chat_people_user()`
- `fenix_prod_profile_get_user()`
- `fenix_prod_profile_socials_get_user()`
- `fenix_prod_session_context()`

Disposition: **INTENTIONAL_AUTHENTICATED_BOUNDARY / RETAIN_PENDING_APP_CALLER_MAP**. Do not convert to `SECURITY INVOKER` blindly because `fenix_prod` tables currently use RLS fail-closed/no-policy patterns and changing execution context could break live reads.

## Mutating authenticated self-service surfaces

These are mutators, all bind to `auth.uid()`, and all include identity, ownership, membership, role, scope, duplicate/version, or storage-path checks appropriate to their contract:

- `fenix_prod_chat_attachment_add_user(...)`
- `fenix_prod_chat_attachment_add_v2_user(...)`
- `fenix_prod_chat_conversation_create_user(...)`
- `fenix_prod_chat_group_create_user(...)`
- `fenix_prod_chat_send_v2_user(...)`
- `fenix_prod_contact_create_v2(...)`
- `fenix_prod_inmo_followup_update_v1(...)`
- `fenix_prod_profile_socials_update_user(jsonb)`
- `fenix_prod_profile_update_user(jsonb)`

Additional live controls observed in definitions include conversation membership/ownership, actor-role checks, zone/owner checks, optimistic version conflict handling, idempotency handling, duplicate-contact checks, storage path bound to authenticated UID, and self-profile scoping.

Disposition: **INTENTIONAL_AUTHENTICATED_SELF_SERVICE / MIGRATION_CANDIDATE_ONLY_AFTER_CALLER_PARITY**. Do not revoke `authenticated` EXECUTE until live caller inventory + gateway/wrapper parity + authenticated HTTP E2E + rollback/cleanup evidence are green.

## Security conclusion

The 16 warnings are **not classified as anonymous exposure**. The prior anonymous finding remains closed: `anon EXECUTE = false` for all 16 audited surfaces.

They remain WARN/fail-closed because the provider linter correctly flags the privilege shape of authenticated `SECURITY DEFINER` functions, and because caller migration/retirement proof is not yet complete. This evidence does **not** mark global SECURITY green and does **not** authorize bulk revocation.

## Next gate

Required before privilege retirement on any mutator:

1. exact live caller map;
2. equivalent server/gateway route proven;
3. authenticated HTTP E2E using controlled identity;
4. cleanup or rollback proof for the write;
5. selective revoke of only the migrated function;
6. post-change E2E + Security Advisor rerun.

This preserves `CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR` and avoids destructive/bulk security changes.
