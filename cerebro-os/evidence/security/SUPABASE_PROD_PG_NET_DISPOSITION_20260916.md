# Supabase PROD · pg_net disposition · 2026-09-16

Status: POR AUDITAR PARA CAMBIO · no mutation applied.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Live read-only evidence

Supabase Security Advisor reports `extension_in_public` for `pg_net`.

Live catalog inspection shows:

- extension: `pg_net`
- version: `0.20.4`
- extension metadata schema: `public`
- `extrelocatable = false`
- extension-owned functions are physically in schema `net`
- extension-owned tables/sequences are physically in schema `net`

Observed extension-owned relations:

- `net.http_request_queue_id_seq`
- `net._http_response`
- `net.http_request_queue`

Observed extension-owned functions include:

- `net.http_get`
- `net.http_post`
- `net.http_delete`
- `net.http_collect_response`
- `net.worker_restart`
- `net.check_worker_is_up`
- internal helpers in `net`

## Disposition

No automatic `ALTER EXTENSION ... SET SCHEMA` is authorized or technically justified from current evidence because the extension declares itself non-relocatable. The Advisor warning refers to extension metadata namespace, while the callable/runtime objects inspected are already isolated under `net`.

Blind drop/recreate or catalog manipulation is rejected because it could break database HTTP jobs, triggers, cron/workflows, or provider-managed extension state.

Before any change to this warning, require:

1. caller/dependency inventory for `net.http_*` and queue tables;
2. backup/rebuild procedure for the extension and dependent objects;
3. provider-supported relocation/reinstall path, if one exists for this project/version;
4. non-PROD rehearsal or equivalent rollback proof;
5. post-change application smoke and Advisor rerun.

Until those gates are proven, this warning remains explicitly classified as `PRESERVE_AND_AUDIT`, not as a reason to mutate PROD.

## Preservation statement

No function, extension, schema, table, data, RLS policy, App/CRM source, Edge Function, or PROD promotion flag was modified by this audit.