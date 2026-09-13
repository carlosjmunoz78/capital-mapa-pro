# CEREBRO OS · Supabase pg_net security audit · 2026-09-14

## Scope
Read-only live audit of `pg_net` in main Supabase project `cluhljgonannaafpmblx`. No extension move, drop/recreate, privilege revoke, schema mutation or PROD behavior change was executed.

## HECHO / live evidence
- Installed extension: `pg_net` version `0.20.4`.
- Extension metadata currently reports schema `public`.
- The installed version reports `relocatable = false`; therefore an `ALTER EXTENSION ... SET SCHEMA` style relocation must not be assumed safe or available.
- Extension relations are physically in schema `net`, including `_http_response`, `http_request_queue` and `http_request_queue_id_seq`.
- Application/user-defined function source search outside `net` found only the Supabase-managed event-trigger helper `extensions.grant_pg_net_access()` referencing `net.*`; no Fénix application RPC caller was found by that read-only function-source search.
- The helper grants schema usage and, for older pg_net versions, function privileges. Current installed version is newer (`0.20.4`), so its old-version SECURITY DEFINER hardening branch does not apply to this installation.
- Current `net` functions are not SECURITY DEFINER.
- Current privilege inspection shows `anon`, `authenticated` and `service_role` have EXECUTE on the inspected `net` functions, including `http_get`, `http_post`, `http_delete`, response helpers and worker helpers.
- No `cron.job` relation exists in this project, so no pg_cron caller evidence was obtained from that path.

## PARCIAL / safety classification
- The Supabase advisor warning about an extension in `public` is real, but the extension is non-relocatable and its owned relations/functions already use `net`; a blind move/drop/recreate would violate the project preservation rule.
- Broadly revoking extension-managed privileges is not authorized as a bulk action and could alter Supabase-managed behavior. It remains blocked until dependency, compatibility and rollback evidence exists.
- Absence of an application RPC source caller is not proof that no external SQL client, provider component or internal platform mechanism uses `pg_net`.

## Required gate before any change
1. Preserve extension/version/object inventory and current grants.
2. Verify provider-supported remediation for the advisor finding for pg_net 0.20.4.
3. Map non-function dependencies and any external/provider callers.
4. Obtain provider restore/rollback evidence before destructive recreation.
5. Rehearse the exact change outside PROD with OLD vs NEW behavior.
6. Apply only a narrowly scoped change with rollback; never bulk-revoke by pattern.

## State
- Dependency inventory: **PARCIAL / READ_ONLY_EVIDENCE_GREEN**.
- Extension relocation: **BLOCKED / NON_RELOCATABLE**.
- Blind drop/recreate: **NOT ALLOWED**.
- Blind privilege revoke: **NOT ALLOWED**.
- PROD mutation performed: **NO**.
- Additional cost introduced: **0 EUR**.
