# CEREBRO OS · PROD security/performance audit · 2026-09-11

## Scope

Read/write remediation performed only where reversible and contract-preserving. App/CRM functional behavior was not redesigned. Secrets are never committed.

## GREEN / remediated

- `social-lead-ingest`: hardcoded shared secret removed from Edge Function source; authentication now resolves against Supabase Vault through a service-role-only verifier. Make caller migrated to the rotated credential. Old credential no longer authenticates.
- `fenix-web-lead`: version 3 adds 64 KiB request cap and calls `fenix_prod_web_lead_ingest_guarded_server`; guard allows at most 10 attempts/hour per normalized identity before delegating to the unchanged canonical ingest RPC.
- `fenix_prod_web_lead_ingest_guarded_server`: `anon=false`, `authenticated=false`, `service_role=true`; invalid identity returns 422 without side effect.
- Six missing FK indexes added additively: activity_log.actor_code, actor_profiles.updated_by_actor_code, chat_attachments.uploader_actor_code, chat_conversations.created_by_actor_code, daily_report_snapshots.scope_actor_code, weekly_report_snapshots.scope_actor_code. `unindexed_foreign_keys` advisor cleared.
- `verify_jwt=false` Edge Functions audited:
  - `fenix-app-gateway`: custom Bearer JWT validation via Supabase Auth before protected routes.
  - `fenix-whatsapp-webhook`: Meta verification token for GET and HMAC SHA-256 signature validation for POST.
  - `social-lead-ingest`: Vault-backed shared-key authentication.
  - `fenix-brevo-inventory-once` / `fenix-brevo-probe-once`: retired endpoints, always HTTP 410.
  - `fenix-web-lead`: public lead form endpoint with origin allowlist, honeypot, payload cap, identity validation, idempotency and rate guard.

## EXISTING / intentional design warnings

- 39 `fenix_prod` tables have RLS enabled with no policies. `anon` and `authenticated` do not have schema/table access; access is mediated by RPC/Edge Functions. Do not add permissive policies merely to silence the linter.
- SECURITY DEFINER user-facing RPCs were classified. User/direct functions include `auth.uid()` or actor binding checks. Nine `_server` findings use actor-binding guards but are still executable by `authenticated`; caller inventory must be completed before revocation so App/CRM is not broken.

## PARTIAL / pending dependency closure

- Make WordPress webhook shared secret is hardcoded in two scenarios: 9694504 (active read) and 9694499 (inactive transport). Same fingerprint; no raw value stored in CEREBRO. Connector security prevented secret exfiltration to Vault. Active read webhook shows no executions after 2026-08-22 and no caller was found in CEREBRO repository. Preserve until caller is confirmed, then rotate both consumers together.
- `pg_net` is installed in `public`, `extrelocatable=false`, with 28 extension-owned objects. No Fénix function/procedure caller was found. Do not drop/recreate in PROD without backup, dependency snapshot, restore test and controlled migration.
- Supabase Auth leaked-password protection is disabled. This is an Auth configuration setting, not a SQL migration.
- Auth DB connection allocation uses an absolute count rather than percentage; informational until instance scaling is planned.
- Unused-index findings are not deletion instructions. Keep indexes until sufficient workload history proves safe removal.

## Rollback notes

- `fenix-web-lead` rollback: redeploy prior Edge version calling `fenix_prod_web_lead_ingest_server`; wrapper is additive and can remain unused.
- FK index rollback: drop only the six named additive indexes if a demonstrated regression appears; no table/constraint data was changed.
- Social lead secret rotation: active value is held by Vault; previous hardcoded credential was intentionally invalidated.

## Promotion rule

No warning is converted to GREEN solely by documentation. Security warnings remain PARTIAL until behavior/dependency evidence justifies remediation or explicit architectural exception.
