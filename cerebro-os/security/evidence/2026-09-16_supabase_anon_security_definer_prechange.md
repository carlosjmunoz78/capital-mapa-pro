# CEREBRO OS · Supabase PROD security snapshot before remediation

Date: 2026-09-16
Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`)
Change class: SECURITY_INCIDENT / HIGH_RISK
Authorization: explicit user authorization received before PROD remediation.

## Scope

Exactly three current Supabase Security Advisor findings of type `anon_security_definer_function_executable`:

1. `public.fenix_prod_profile_goal_set_server(text,text,text,text,integer,text)`
2. `public.fenix_prod_profile_goals_get_server(text,text)`
3. `public.fenix_prod_user_admin_update_server(text,text,text,text,boolean)`

No App/CRM data mutation is part of this remediation. The intended change is ACL-only: remove direct REST execution from `PUBLIC`, `anon`, and `authenticated` for these `_server` RPCs while retaining `service_role`.

## Live caller inventory

Supabase Edge Function `fenix-profile-api` v2 calls `fenix_prod_profile_goals_get_server` through a Supabase client initialized with `SUPABASE_SERVICE_ROLE_KEY`, after validating the user's bearer token and resolving `actorCode` through `fenix_prod_actor_context_by_auth_server`.

Supabase Edge Function `fenix-user-admin` v3 calls both `fenix_prod_user_admin_update_server` and `fenix_prod_profile_goal_set_server` through a Supabase client initialized with `SUPABASE_SERVICE_ROLE_KEY`, after validating the bearer token, resolving actor context, and enforcing `Direccion` plus the canonical admin actors.

Repository code search on the accessible default branch returned no direct source callers for the three `_server` RPC names. This does not prove absence outside inspected surfaces; therefore the remediation preserves the server-side Edge Function path and changes only direct database execute grants.

## Pre-change ACL snapshot

`fenix_prod_profile_goal_set_server`:
`=X/postgres,postgres=X/postgres,anon=X/postgres,authenticated=X/postgres,service_role=X/postgres`

`fenix_prod_profile_goals_get_server`:
`=X/postgres,postgres=X/postgres,anon=X/postgres,authenticated=X/postgres,service_role=X/postgres`

`fenix_prod_user_admin_update_server`:
`=X/postgres,postgres=X/postgres,anon=X/postgres,authenticated=X/postgres,service_role=X/postgres`

All three are `SECURITY DEFINER` and already set an explicit `search_path`.

## Definition snapshot summary

### `fenix_prod_profile_goal_set_server`

Current function authorizes a supplied `p_actor_code` by looking it up in `fenix_prod.actors`, requires role `Direccion`, and restricts actor code to `CARLOS-ADMIN` or `BELEN-DIR`. It writes performance goals and activity log. It does not itself bind `p_actor_code` to an authenticated JWT. The supported Edge Function caller performs bearer-token validation and actor-context resolution before invoking it with service role.

### `fenix_prod_profile_goals_get_server`

Current function looks up the supplied `p_actor_code`, computes monthly goals and actuals, and returns JSON. It does not itself bind `p_actor_code` to an authenticated JWT. The supported Edge Function caller performs bearer-token validation and actor-context resolution before invoking it with service role.

### `fenix_prod_user_admin_update_server`

Current function begins by calling `public.fenix_prod_actor_binding_guard(p_actor_code)` and then enforces `Direccion` / canonical admin restrictions and target protections. The supported Edge Function caller also validates the bearer token and actor context before invoking it with service role.

## Planned forward migration

```sql
REVOKE EXECUTE ON FUNCTION public.fenix_prod_profile_goal_set_server(text,text,text,text,integer,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fenix_prod_profile_goal_set_server(text,text,text,text,integer,text) TO service_role;

REVOKE EXECUTE ON FUNCTION public.fenix_prod_profile_goals_get_server(text,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fenix_prod_profile_goals_get_server(text,text) TO service_role;

REVOKE EXECUTE ON FUNCTION public.fenix_prod_user_admin_update_server(text,text,text,text,boolean) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fenix_prod_user_admin_update_server(text,text,text,text,boolean) TO service_role;
```

## Exact ACL rollback

If supported application behavior regresses, restore only the prior grants:

```sql
GRANT EXECUTE ON FUNCTION public.fenix_prod_profile_goal_set_server(text,text,text,text,integer,text) TO PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.fenix_prod_profile_goals_get_server(text,text) TO PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.fenix_prod_user_admin_update_server(text,text,text,text,boolean) TO PUBLIC, anon, authenticated, service_role;
```

Rollback does not alter function definitions or data.

## Required post-change gates

- catalog ACL confirms no `PUBLIC`/`anon`/`authenticated` EXECUTE on the three RPCs;
- service role retains EXECUTE;
- Supabase Security Advisor reports zero `anon_security_definer_function_executable` findings for these functions;
- Edge Function supported paths remain present and unchanged;
- no claim that the overall SECURITY group is green until remaining findings/gates are resolved.