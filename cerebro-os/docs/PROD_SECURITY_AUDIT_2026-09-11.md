# CEREBRO OS · PROD security/performance audit · 2026-09-11

## Scope

Evidence-first PROD audit. Remediation is applied only when reversible and contract-preserving. App/CRM functional behavior is preserved. No raw secret is committed. Warnings are not declared GREEN solely because documentation exists.

## GREEN / remediated

### Credentials and public ingress

- `social-lead-ingest` v5: former hardcoded shared secret removed from Edge source. Authentication resolves against Supabase Vault through a service-role-only verifier. Make scenario 9768402/module 8 uses the rotated credential. The former credential no longer authenticates.
- `fenix-web-lead` v3: 64 KiB request cap + honeypot + origin allowlist + idempotency + `fenix_prod_web_lead_ingest_guarded_server`. Guard rate-limits the same normalized identity to 10 attempts/hour before delegating to the unchanged canonical ingest RPC.
- `fenix_prod_web_lead_ingest_guarded_server`: `anon=false`, `authenticated=false`, `service_role=true`; invalid identity test returned 422 with no side effect.
- All six active `verify_jwt=false` Edge Functions were inspected:
  - `fenix-app-gateway`: `/health` public; protected routes validate Bearer JWT with Supabase Auth and resolve actor binding.
  - `fenix-whatsapp-webhook`: Meta challenge for GET and HMAC SHA-256 signature verification for POST.
  - `social-lead-ingest`: Vault-backed shared-key authentication.
  - `fenix-web-lead`: intentionally public lead form with the controls above.
  - `fenix-brevo-inventory-once` / `fenix-brevo-probe-once`: retired; always HTTP 410.

### Database / PostgREST authorization

- Nine backend-only SECURITY DEFINER RPC signatures had unnecessary `authenticated` execution revoked in migration `restrict_backend_server_rpcs_v1`; `service_role` retains execution. The security advisor dropped from 33 to 24 SECURITY DEFINER findings.
- Exact public API surface verified live:
  - **0** `public` functions of any kind executable by `anon`.
  - **0** `public` tables/views with direct grants to `anon` or `authenticated`.
  - Exactly **24** functions executable by `authenticated`; all 24 are SECURITY DEFINER, all are intentional user-facing RPCs, and there are **0** SECURITY INVOKER functions exposed to `authenticated`.
  - 24/24 contain identity control (`auth.uid()` / actor binding), all have fixed `search_path`, and neither `anon`, `authenticated` nor PUBLIC can `CREATE` in `public`.
- The 24 authenticated user RPCs were functionally reviewed by family: ANA approved knowledge, chat, contact creation, expediente create/update, inmobiliaria follow-up, notification state/list, self profile/socials, session context and signature workflow creation.
- `fenix_prod_special_case_confirm_sensitive_server` is service-role-only. Ordinary special-case updates return `SIGNATURE_REQUIRED` for signature transitions and `LEGAL_REQUIRED` for legal close. API v9 exposes explicit human confirmation only to `Direccion` and requires `evidence_ref`.
- Signature workflow verified: creation only creates a workflow; scheduling requires FEIN/plazo/checklist/notary; confirmation requires checklist; final close requires `Direccion`, `gate_cierre_belen='Liberado'`, prior confirmation and version match. Confirm/close RPCs are service-role-only and are reached through authenticated `fenix-app-gateway`.
- Bank workflow verified: prepare is idempotent; authorization requires `Direccion` and unchanged payload hash; actual bank send remains deliberately blocked with `transport_not_configured`; offer acceptance/rejection requires `Direccion`, version and reason. Appraisal validation also requires `Direccion` and reason.

### Storage

- `fenix-prod-documents`: private bucket, 50 MiB limit, explicit document/image/text MIME allowlist; no direct authenticated Storage policy. Document access is mediated through signed URLs/Edge functions.
- `fenix-prod-chat`: private bucket, 20 MiB limit, explicit MIME allowlist. Authenticated INSERT/DELETE is restricted to the caller's own `auth.uid()` folder. SELECT requires the attachment to belong to EQUIPO or to a conversation where the actor is a member.
- Chat RPCs were reviewed: conversation membership is required for v2 reads/writes; group creation validates active members and includes the creator; message size and idempotency are bounded.
- Found and fixed one integrity inconsistency: `fenix_prod_chat_attachment_add_v2_user` previously validated owner/path/size but not declared MIME. Migration `chat_attachment_v2_mime_validation_v1` now applies the same MIME allowlist as the bucket and legacy attachment RPC.

### AI / document intelligence human gates

Historical evidence from `fenix_prod.document_intelligence_runs`: 65 `applied` runs had minimum confidence 0.95 and median 0.99. This evidence established policy V1 rather than embedding an arbitrary threshold in Edge code.

- Added closed table `fenix_prod.runtime_policies`; no public/anon/authenticated grants, RLS on, service-role read only.
- Added service-only `fenix_prod_runtime_policy_server(text)`.
- Active policy `document_auto_ingest_min_confidence` V1 = 0.95 with rationale stored in DB.
- `fenix-document-auto-ingest` v2: policy unavailable/invalid => `POLICY_CONFLICT`; confidence missing/below policy => `needs_review`, HTTP 409, `HUMAN_REQUIRED / LOW_CONFIDENCE`, no canonical write.
- `fenix-document-intelligence` v12: `/apply` has the same central confidence gate before any canonical update.
- `fenix-document-extract` v12: low confidence cuts before `/apply` and before direct canonical-field RPC; if `/apply` returns review, no lateral field write occurs.
- `fenix-document-reread` v2: restricted to `Direccion/Financiero`; appraisal rereads use the same policy and low confidence cannot be marked applied.
- `fenix-document-existing-backfill` is bounded (max 4 per run), role-restricted and now flows through the confidence-protected auto-ingest path.
- `fenix-document-intelligence-test` is fail-isolated by slug and returns before any write.

### Data integrity / workflow gates

- `fenix_prod_task_update_server`: update now validates canonical task states and criticities; ownership/version gates are preserved.
- `fenix_prod_exp_stage_server`: stages are limited to the union of live/historical canonical values; expected version is mandatory; stage history is preserved.
- `fenix_prod_exp_update_server`: bypass closed. It now uses the same stage catalog, validates inmobiliaria references, requires version and writes stage history. Fail-closed test with an invalid stage returned 400 and preserved both stage and version unchanged.
- `fenix_prod_document_edit_server`: role/ownership/version/move controls and `document_change_history` are intact; DB already constrains document sensitivity. Open `tipo/estado/calidad` fields are not frozen to an invented incomplete enum.
- `fenix-directory-actions`: only `Direccion`; manual records are marked `nivel_verificacion='manual_app'` and do not impersonate official sources.
- Directory read RPCs for notaries/registries/personal restrict access to `Direccion/Financiero`.
- B2B writes enforce role/owner/zone scope, deduplication and `Validado contra origen=false`.
- Notification reads/actions enforce actor ownership except Dirección company visibility; inmobiliaria follow-up enforces Dirección/Visitador owner-or-zone scope plus optimistic version.
- Self-profile/social RPCs are bound to `auth.uid()` and update only the caller's actor; profile changes are logged in `activity_log`.

### Knowledge / ANA governance

- `fenix-ana-canonical` is read-only and returns only canonical, approved, applied, non-TEST rules.
- `fenix-memory-api` can record authorized context but stores it as non-origin-validated context, not as an auto-promoted canonical rule.
- `fenix-ana-knowledge` creates candidates at low initial confidence and requires explicit review; Hipotecas/Finanzas are routed to Belén authority.
- `fenix_prod_ana_correction_decide_v2_server`: only `Direccion` can decide a candidate; version and idempotency gates prevent silent re-review.
- `fenix_prod_ana_knowledge_answer_user` reads only approved knowledge cards or approved correction rules; pending candidates are not answer sources.

### Edge inventory

All 38 currently active Edge Functions in `fenix-capital-prod` were inventoried. Write/high-risk surfaces were inspected individually; retired one-shot sync/migration endpoints return HTTP 410; read APIs authenticate and scope by actor/role. No additional hardcoded secret was found in the inspected Edge source.

### Performance

- Added six missing FK indexes additively: `activity_log.actor_code`, `actor_profiles.updated_by_actor_code`, `chat_attachments.uploader_actor_code`, `chat_conversations.created_by_actor_code`, `daily_report_snapshots.scope_actor_code`, `weekly_report_snapshots.scope_actor_code`.
- `unindexed_foreign_keys` advisor cleared after migration.
- Current performance advisor contains only `unused_index` INFO findings and `auth_db_connections_absolute` INFO. `unused_index` is not a deletion instruction; newly created indexes also appear unused until workload reaches them.

## EXISTING / intentional architectural warnings

- 40 `fenix_prod` tables report `RLS enabled, no policy`; `runtime_policies` uses the same closed-table pattern. This is intentional because the schema/tables are not directly granted to `anon/authenticated`; access is mediated by controlled RPC/Edge functions. Do not add permissive policies merely to silence the linter.
- 24 authenticated SECURITY DEFINER findings remain intentionally as the complete user-facing RPC surface. Each has identity control and fixed `search_path`; backend-only functions were removed from authenticated execution.
- `fenix-reports-api`: Dirección receives company scope; Financiero/Visitador actor scope only. Snapshot refresh is reporting materialization, not business mutation.

## PARTIAL / pending external or destructive dependency closure

- Make WordPress webhook shared secret remains hardcoded in two scenarios: 9694504 (active read) and 9694499 (inactive transport), same fingerprint. Raw transfer to Vault is blocked by connector security controls. No executions observed on the active read webhook after 2026-08-22 and no caller found in accessible CEREBRO/GitHub/Make scenario inventory. Preserve until caller is confirmed; rotate both consumers together. Do not print or commit the value.
- `pg_net` is installed in `public`, `extrelocatable=false`, with 28 extension-owned objects. No Fénix function/procedure caller was found. Drop/recreate is intentionally blocked pending backup, dependency snapshot, restore test and controlled migration.
- Supabase Auth leaked-password protection is disabled. Supabase documents it as a Pro-or-higher capability; current connector does not expose the project billing plan or an Auth-config mutation. Do not add a new subscription solely to silence the warning.
- Both legacy anon and modern publishable client keys remain active. No accessible repository hardcodes the PROD project ref, but deployed frontend inventory is incomplete; do not revoke the legacy client key blindly.
- Auth DB connection allocation uses an absolute count rather than percentage; informational until instance scaling is planned.
- The current Supabase connector does not expose backup/restore operations, so a live provider restore drill cannot be truthfully claimed from this session.

## Advisor snapshot after remediation

- Security: 40 `rls_enabled_no_policy` INFO (intentional closed-table pattern), 1 `pg_net` WARN, 24 authenticated SECURITY DEFINER WARN (intentional audited user surface), 1 leaked-password protection WARN.
- Performance: 40 `unused_index` INFO, 1 Auth absolute-connection allocation INFO; **0 unindexed foreign-key findings**.

## Rollback notes

- `fenix-web-lead`: redeploy prior Edge version calling `fenix_prod_web_lead_ingest_server`; abuse guard is additive.
- Document confidence changes: prior Edge versions remain recoverable; runtime policy is versioned. Removing the gate requires an explicit policy decision because LOW_CONFIDENCE protection is now a governance requirement.
- Backend RPC EXECUTE revocation: rollback is targeted `GRANT EXECUTE` on the exact former signatures.
- Stage/task/chat validation: rollback is `CREATE OR REPLACE` to prior function body; no destructive table/data migration was required.
- FK indexes: drop only the six named additive indexes if a demonstrated regression appears.
- Social lead secret rotation: active value is held by Vault; previous hardcoded credential was intentionally invalidated.

## Promotion rule

No warning becomes GREEN by documentation alone. GREEN above means a live contract, permission, Edge version, SQL check or advisor result was inspected/tested. External/destructive unknowns remain PARTIAL until equivalent evidence exists.
