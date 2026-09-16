# Supabase PROD · authenticated SECURITY DEFINER caller map · 2026-09-16

Status: PARCIAL · read-only/live evidence capture. No PROD mutation performed in this step.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Scope

This evidence refines the disposition of the 16 remaining `SECURITY DEFINER` functions executable by `authenticated`. The objective is selective retirement only after each live caller is identified and an equivalent authenticated route has passed parity + HTTP E2E + rollback.

## Live Edge Function evidence

### `fenix-app-gateway` v18

The live gateway authenticates the bearer token, resolves identity server-side through `fenix_prod_actor_context_by_auth_server`, and then invokes service-role-only `*_server` wrappers for application routes.

Relevant proven replacements include:

- session context route: `/session/context` -> `fenix_prod_session_context_server`;
- contact creation route: `/contactos` POST -> `fenix_prod_contact_create_server`;
- chat route: `/chat` GET/POST -> `fenix_prod_chat_list_server` / `fenix_prod_chat_send_server`;
- inmobiliaria routes use `fenix_prod_inmo_*_server` wrappers.

The v18 source inspected in Supabase contains no direct call to any of the 16 legacy authenticated SECDEF names.

### `fenix-profile-api` v2

The live profile Edge Function validates the bearer token, resolves the actor with service role, and calls only server wrappers:

- `fenix_prod_profile_get_full_server`;
- `fenix_prod_profile_update_full_server`;
- `fenix_prod_profile_goals_get_server`.

No direct call to legacy `fenix_prod_profile_get_user`, `fenix_prod_profile_socials_get_user`, `fenix_prod_profile_socials_update_user`, or `fenix_prod_profile_update_user` is present in the inspected live source.

### `fenix-ana-knowledge` v9

A live direct caller still exists for one legacy authenticated SECDEF surface:

- `fenix_prod_session_context()` is called through an authenticated Supabase client in `fenix-ana-knowledge`.

Therefore `fenix_prod_session_context()` MUST NOT have `authenticated EXECUTE` revoked yet. The correct retirement sequence is:

1. migrate `fenix-ana-knowledge` to a server-wrapper/identity-equivalent path;
2. prove behavior parity;
3. prove authenticated HTTP E2E;
4. retain rollback;
5. only then revoke the legacy authenticated EXECUTE and rerun the Supabase advisor.

## Current selective disposition

- `fenix_prod_session_context`: `KEEP_UNTIL_LIVE_CALLER_MIGRATED`.
- profile legacy functions: `CANDIDATE_FOR_SELECTIVE_RETIREMENT`, but only after confirming no additional live callers outside the inspected Edge surfaces and after HTTP E2E of the replacement path.
- chat/contact/inmo legacy functions: `CANDIDATE_OR_KEEP_BY_CONTRACT`; gateway replacement evidence exists for parts of these domains, but exact per-function source caller coverage is not yet complete.
- all remaining surfaces: no bulk revoke and no mass conversion to `SECURITY INVOKER`.

## Search limitation

GitHub code search for the legacy names returned no indexed repository caller matches, but this is not treated as proof of absence because code search reported incomplete/empty results and live Supabase Edge Functions are authoritative runtime evidence.

## Preservation statement

No function ACL, function body, schema, table, RLS policy, Edge Function deployment, App/CRM source, customer data, secret, or promotion flag was changed by this caller-map step.
