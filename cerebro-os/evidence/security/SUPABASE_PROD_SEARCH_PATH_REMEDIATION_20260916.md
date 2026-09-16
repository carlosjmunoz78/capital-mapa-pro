# Supabase PROD · search_path remediation · 2026-09-16

Status: HECHO · PROD security remediation explicitly authorized.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Pre-change snapshot

Two Supabase Security Advisor `function_search_path_mutable` warnings were present:

- `public.fenix_prod_task_order_bucket(text)`
- `public.fenix_prod_expediente_is_active(text, boolean)`

Both functions were `SECURITY INVOKER`/non-`SECURITY DEFINER`, `IMMUTABLE`, had `proconfig = NULL`, and their definitions contained only deterministic built-in expression logic. A `pg_depend` read-only inventory showed only the namespace dependency and no table/object dependency requiring an application schema in `search_path`.

Original configuration rollback contract for both functions:

```sql
ALTER FUNCTION public.fenix_prod_task_order_bucket(text) RESET search_path;
ALTER FUNCTION public.fenix_prod_expediente_is_active(text, boolean) RESET search_path;
```

No function body replacement was required.

## Applied migration

Migration: `harden_function_search_path_20260916`

```sql
ALTER FUNCTION public.fenix_prod_task_order_bucket(text)
  SET search_path = pg_catalog, pg_temp;

ALTER FUNCTION public.fenix_prod_expediente_is_active(text, boolean)
  SET search_path = pg_catalog, pg_temp;
```

## Post-change evidence

Supabase Security Advisor was rerun immediately after migration. The `function_search_path_mutable` category is absent: warning count reduced from 2 to 0.

The remaining WARN categories are intentionally not bulk-remediated:

- `authenticated_security_definer_function_executable`: 16 surfaces pending caller/contract disposition;
- `extension_in_public`: `pg_net`, pending dependency + backup/rebuild review;
- `auth_leaked_password_protection`: pending supported Auth configuration write channel.

`RLS Enabled No Policy` findings remain INFO/fail-closed and are not treated as proof of open access.

## Preservation statement

This migration did not alter App source, CRM source, function bodies, table data, RLS policies, Edge Functions, authentication identities, or global PROD promotion state.
