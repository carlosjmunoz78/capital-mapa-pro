# CEREBRO OS · PROD security/performance audit · 2026-09-11

## Scope

Evidence-first PROD audit. Remediation is applied only when reversible and contract-preserving. App/CRM functional behavior is preserved. No raw secret is committed. Warnings are not declared GREEN solely because documentation exists.

## GREEN / remediated

### Credentials and public ingress

- `social-lead-ingest` v5: former hardcoded shared secret removed from Edge source. Authentication resolves against Supabase Vault through a service-role-only verifier. Make scenario 9768402/module 8 uses the rotated credential. The former credential no longer authenticates.
- `fenix-web-lead` v3: 64 KiB request cap + honeypot + origin allowlist + idempotency + `fenix_prod_web_lead_ingest_guarded_server`. Guard rate-limits the same normalized identity to 10 attempts/hour before delegating to the unchanged canonical ingest RPC.
- `fenix_prod_web_lead_ingest_guarded_server`: `anon=false`, `authenticated=false`, `service_role=true`; invalid identity test returned 422 with no side effect.
- All six active `verify_jwt=false` Edge Functions were inspected: `fenix-app-gateway` validates protected routes with Supabase Auth; `fenix-whatsapp-webhook` verifies Meta HMAC; `social-lead-ingest` uses Vault-backed shared-key authentication; `fenix-web-lead` is intentionally public with abuse controls; retired Brevo one-shot endpoints return HTTP 410.

### Database / PostgREST authorization

- Nine backend-only SECURITY DEFINER RPC signatures had unnecessary `authenticated`/`anon` execution revoked in the live hardening change recorded as `lock_backend_only_server_rpcs_20260911`; `service_role` retains execution. The security advisor dropped from 33 to 24 SECURITY DEFINER findings.
- Exact public API surface verified live: 0 `public` functions executable by `anon`; 0 `public` tables/views with direct grants to `anon` or `authenticated`; exactly 24 functions executable by `authenticated`, all intentional user-facing SECURITY DEFINER RPCs with identity control and fixed `search_path`.
- The 24 authenticated user RPCs were functionally reviewed by family: ANA approved knowledge, chat, contact creation, expediente create/update, inmobiliaria follow-up, notification state/list, self profile/socials, session context and signature workflow creation.
- Sensitive special-case, signature, bank, offer and appraisal transitions preserve role/version/evidence/human gates. Actual bank transport remains deliberately blocked with `transport_not_configured`.

### Storage

- `fenix-prod-documents` and `fenix-prod-chat` are private, MIME/size bounded and mediated through controlled RPC/Edge/storage policies. Chat membership and uploader ownership are enforced.
- `fenix_prod_chat_attachment_add_v2_user` MIME validation was aligned with the bucket/legacy attachment contract.

### AI / document intelligence human gates

Historical evidence from `fenix_prod.document_intelligence_runs`: 65 `applied` runs had minimum confidence 0.95 and median 0.99. Runtime policy `document_auto_ingest_min_confidence` V1 = 0.95 is stored centrally. Missing/invalid policy fails with `POLICY_CONFLICT`; confidence below policy routes to `HUMAN_REQUIRED / LOW_CONFIDENCE` before canonical writes. Auto-ingest, intelligence apply, extract, reread and bounded backfill preserve that gate.

### Data integrity / workflow gates

Task/stage/document updates preserve canonical state validation, optimistic versioning, ownership/role scope and history. Directory manual records do not impersonate official sources. B2B writes preserve scope/dedup/source-validation flags. Notification and profile actions are actor-scoped.

### Knowledge / ANA governance

Canonical ANA reads only approved/applied/non-test knowledge. Memory context is not auto-promoted. Knowledge corrections require explicit review; Hipotecas/Finanzas route to Belén authority; only Dirección can decide candidates with version/idempotency gates.

### Edge inventory

All 38 currently active Edge Functions in `fenix-capital-prod` were inventoried. Write/high-risk surfaces were inspected individually; retired one-shot sync/migration endpoints return HTTP 410; read APIs authenticate and scope by actor/role. No additional hardcoded secret was found in the inspected Edge source.

### Performance

- Added six missing FK indexes additively: `activity_log.actor_code`, `actor_profiles.updated_by_actor_code`, `chat_attachments.uploader_actor_code`, `chat_conversations.created_by_actor_code`, `daily_report_snapshots.scope_actor_code`, `weekly_report_snapshots.scope_actor_code`.
- `unindexed_foreign_keys` advisor cleared after migration.
- Current performance advisor contains only `unused_index` INFO findings and `auth_db_connections_absolute` INFO. `unused_index` is not a deletion instruction.

## EXISTING / intentional architectural warnings

- 40 `fenix_prod` tables report `RLS enabled, no policy`; this is an intentional closed-table pattern because schema/tables are not directly granted to `anon/authenticated`; access is mediated by controlled RPC/Edge functions.
- 24 authenticated SECURITY DEFINER findings remain intentionally as the complete audited user-facing RPC surface.
- `fenix-reports-api`: Dirección receives company scope; Financiero/Visitador actor scope only.

## PARTIAL / pending external or destructive dependency closure

- Make WordPress webhook shared secret remains hardcoded in two scenarios: 9694504 (active read) and 9694499 (inactive transport), same fingerprint. Accessible Make history shows successful executions only on 2026-08-22 and no retained delivery headers/IP identifying the caller. Preserve until caller is confirmed; rotate both consumers together. Do not print or commit the value.
- `pg_net` is installed in `public`, `extrelocatable=false`, with 28 extension-owned objects. No Fénix function/procedure caller was found. Drop/recreate is blocked pending backup, dependency snapshot, restore test and controlled migration.
- Supabase Auth leaked-password protection is disabled. Current connector does not expose Auth-config mutation; no new subscription is introduced solely to silence this warning.
- Both legacy anon and modern publishable client keys remain active. Deployed frontend inventory is incomplete; do not revoke the legacy client key blindly.
- Auth DB connection allocation uses an absolute count rather than percentage; informational until instance scaling is planned.
- Current Supabase connector does not expose provider backup/restore operations, so a live provider restore drill cannot be truthfully claimed from this session.
- Legacy `fenix-capital-inmo-map` warnings are predominantly `preprod_test`/`*_preprod`. App PREPROD is cancelled; these resources are preserved and are not reactivated or mutated by this audit.

## Advisor snapshot after remediation

- Security: 40 `rls_enabled_no_policy` INFO (intentional closed-table pattern), 1 `pg_net` WARN, 24 authenticated SECURITY DEFINER WARN (intentional audited user surface), 1 leaked-password protection WARN.
- Performance: `unused_index` INFO plus Auth absolute-connection allocation INFO; 0 unindexed foreign-key findings.

## Rollback notes

- `fenix-web-lead`: redeploy prior Edge version calling `fenix_prod_web_lead_ingest_server`; abuse guard is additive.
- Document confidence changes: prior Edge versions remain recoverable; runtime policy is versioned.
- Backend RPC EXECUTE revocation (`lock_backend_only_server_rpcs_20260911`): rollback is targeted `GRANT EXECUTE` on the exact former signatures only.
- Stage/task/chat validation: rollback is `CREATE OR REPLACE` to prior function body; no destructive table/data migration was required.
- FK indexes: drop only the six named additive indexes if a demonstrated regression appears.
- Social lead secret rotation: active value is held by Vault; previous hardcoded credential was intentionally invalidated.

## Promotion rule

No warning becomes GREEN by documentation alone. GREEN above means a live contract, permission, Edge version, SQL check or advisor result was inspected/tested. External/destructive unknowns remain PARTIAL until equivalent evidence exists.
