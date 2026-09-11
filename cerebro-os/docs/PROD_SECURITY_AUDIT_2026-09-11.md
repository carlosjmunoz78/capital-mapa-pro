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

### Database authorization

- Nine backend-only SECURITY DEFINER RPC signatures had unnecessary `authenticated` execution revoked in migration `restrict_backend_server_rpcs_v1`; `service_role` retains execution. The security advisor dropped from 33 to 24 SECURITY DEFINER findings.
- The remaining 24 authenticated RPCs are intentional user-facing functions. Verified together: 0 executable by `anon`; 24/24 contain identity control (`auth.uid()` / actor binding); all have fixed `search_path`; `anon`, `authenticated` and PUBLIC cannot `CREATE` in `public`.
- `fenix_prod_special_case_confirm_sensitive_server` is service-role-only. Ordinary special-case updates return `SIGNATURE_REQUIRED` for signature transitions and `LEGAL_REQUIRED` for legal close. API v9 exposes explicit human confirmation only to `Direccion` and requires `evidence_ref`.
- Signature workflow verified: creation only creates a workflow; scheduling requires FEIN/plazo/checklist/notary; confirmation requires checklist; final close requires `Direccion`, `gate_cierre_belen='Liberado'`, prior confirmation and version match. Confirm/close RPCs are service-role-only and are reached through authenticated `fenix-app-gateway`.
- Bank workflow verified: prepare is idempotent; authorization requires `Direccion` and unchanged payload hash; actual bank send remains deliberately blocked with `transport_not_configured`; offer acceptance/rejection requires `Direccion`, version and reason. Appraisal validation also requires `Direccion` and reason.

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
- B2B writes enforce role/owner/zone scope, deduplication and `Validado contra origen=false`.

### Knowledge / ANA governance

- `fenix-ana-canonical` is read-only and returns only canonical, approved, applied, non-TEST rules.
- `fenix-memory-api` can record authorized context but stores it as non-origin-validated context, not as an auto-promoted canonical rule.
- `fenix-ana-knowledge` creates candidates at low initial confidence and requires explicit review; Hipotecas/Finanzas are routed to Belén authority.
- `fenix_prod_ana_correction_decide_v2_server`: only `Direccion` can decide a candidate; version and idempotency gates prevent silent re-review.

### Edge inventory

All 38 currently active Edge Functions in `fenix-capital-prod` were inventoried. Write/high-risk surfaces were inspected individually; retired one-shot sync/migration endpoints return HTTP 410; read APIs authenticate and scope by actor/role. No additional hardcoded secret was found in the inspected Edge source.

### Performance

- Added six missing FK indexes additively: `activity_log.actor_code`, `actor_profiles.updated_by_actor_code`, `chat_attachments.uploader_actor_code`, `chat_conversations.created_by_actor_code`, `daily_report_snapshots.scope_actor_code`, `weekly_report_snapshots.scope_actor_code`.
- `unindexed_foreign_keys` advisor cleared after migration.
- `unused_index` findings are not treated as deletion instructions; newly created indexes also appear unused until workload reaches them.

## EXISTING / intentional architectural warnings

- 40 `fenix_prod` tables currently report `RLS enabled, no policy`; the count increased by one because `runtime_policies` uses the same closed-table pattern. `anon` and `authenticated` have no direct useful schema/table access; access is mediated through controlled RPC/Edge functions. Do not add permissive policies merely to silence the linter.
- 24 authenticated SECURITY DEFINER findings remain intentionally as user-facing RPCs with identity checks and fixed `search_path`; the backend-only findings were removed.
- `fenix-reports-api`: Dirección receives company scope; Financiero/Visitador actor scope only. Snapshot refresh is reporting materialization, not business mutation.

## PARTIAL / pending external or destructive dependency closure

- Make WordPress webhook shared secret remains hardcoded in two scenarios: 9694504 (active read) and 9694499 (inactive transport), same fingerprint. Raw transfer to Vault is blocked by connector security controls. No executions observed on the active read webhook after 2026-08-22 and no caller found in accessible CEREBRO/GitHub repos. Preserve until caller is confirmed; rotate both consumers together. Do not print or commit the value.
- `pg_net` is installed in `public`, `extrelocatable=false`, with 28 extension-owned objects. No Fénix function/procedure caller was found. Drop/recreate is intentionally blocked pending backup, dependency snapshot, restore test and controlled migration.
- Supabase Auth leaked-password protection is disabled. Supabase documents it as a Pro-or-higher capability; current connector does not expose the project billing plan or an Auth-config mutation. Do not add a new subscription solely to silence the warning.
- Both legacy anon and modern publishable client keys remain active. No accessible repository hardcodes the PROD project ref, but deployed frontend inventory is incomplete; do not revoke the legacy client key blindly.
- Auth DB connection allocation uses an absolute count rather than percentage; informational until instance scaling is planned.

## Rollback notes

- `fenix-web-lead`: redeploy prior Edge version calling `fenix_prod_web_lead_ingest_server`; abuse guard is additive.
- Document confidence changes: prior Edge versions remain recoverable; runtime policy is versioned. Removing the gate requires an explicit policy decision because LOW_CONFIDENCE protection is now a governance requirement.
- Backend RPC EXECUTE revocation: rollback is targeted `GRANT EXECUTE` on the exact former signatures.
- Stage/task validation: rollback is `CREATE OR REPLACE` to prior function body; no table shape/data migration was required.
- FK indexes: drop only the six named additive indexes if a demonstrated regression appears.
- Social lead secret rotation: active value is held by Vault; previous hardcoded credential was intentionally invalidated.

## Promotion rule

No warning becomes GREEN by documentation alone. GREEN above means a live contract, permission, Edge version, SQL check or advisor result was inspected/tested. External/destructive unknowns remain PARTIAL until equivalent evidence exists.
