# CEREBRO OS · Supabase PROD anon SECURITY DEFINER remediation evidence

Date: 2026-09-16
Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`)
Authorization: explicit user authorization `AUTORIZO REMEDIACIÓN SEGURIDAD PROD`.

## Change applied

Supabase migration:
`harden_anon_security_definer_profile_admin_20260916`

The migration changed only EXECUTE ACLs on these three existing functions:

- `public.fenix_prod_profile_goal_set_server(text,text,text,text,integer,text)`
- `public.fenix_prod_profile_goals_get_server(text,text)`
- `public.fenix_prod_user_admin_update_server(text,text,text,text,boolean)`

`PUBLIC`, `anon`, and `authenticated` direct EXECUTE were revoked. `service_role` EXECUTE was explicitly retained.

No function body, table row, App source, CRM source, Edge Function, RLS policy, or customer data was modified by this migration.

## Post-change catalog proof

For all three functions:

- `anon_execute = false`
- `authenticated_execute = false`
- `service_role_execute = true`
- ACL now equals `{postgres=X/postgres,service_role=X/postgres}`

## Post-change Supabase Security Advisor

After the migration, the advisor no longer returns the `anon_security_definer_function_executable` lint. The previous three anonymous SECURITY DEFINER findings are therefore removed.

The `authenticated_security_definer_function_executable` count decreased from 19 to 16 because the same three `_server` functions are no longer directly executable by `authenticated`.

Remaining advisor categories are deliberately not auto-remediated here:

- 46 `rls_enabled_no_policy` informational findings;
- 16 authenticated SECURITY DEFINER findings requiring caller/contract classification;
- 2 mutable-search-path function warnings;
- `pg_net` extension in `public`;
- leaked-password protection disabled.

These remaining findings are not declared safe or unsafe by this artifact; they remain subject to dependency analysis and fail-closed remediation.

## Supported caller continuity

The live supported callers inspected before the change use Edge Functions with `service_role` after identity/RBAC checks:

- `fenix-profile-api` v2 → `fenix_prod_profile_goals_get_server`
- `fenix-user-admin` v3 → `fenix_prod_profile_goal_set_server`
- `fenix-user-admin` v3 → `fenix_prod_user_admin_update_server`

Because `service_role` retained EXECUTE, the intended server-mediated contract remains available. No direct anonymous or authenticated PostgREST execution remains on these three functions.

## Rollback

The exact prior ACL grants are preserved in the pre-change snapshot artifact and can be restored without changing function bodies or data.

## Status

This incident slice is GREEN: anonymous EXECUTE on the three identified `_server` SECURITY DEFINER RPCs is eliminated with rollback evidence.

Overall global `SECURITY` remains PARTIAL until the remaining security gates are individually classified and closed.