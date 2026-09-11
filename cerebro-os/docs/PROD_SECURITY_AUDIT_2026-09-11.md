# CEREBRO OS · PROD security/performance audit · 2026-09-11

## Scope
Evidence-first PROD audit. Remediation only when reversible and contract-preserving. App/CRM functional behavior preserved. No raw secret committed.

## GREEN / remediated
- `social-lead-ingest` v5: former hardcoded shared secret removed; Vault-backed verifier; Make 9768402 uses rotated credential; former credential invalidated.
- `fenix-web-lead` v3: 64 KiB cap, honeypot, origin allowlist, idempotency and guarded server rate limit.
- Six active `verify_jwt=false` Edge Functions inspected and their internal auth/webhook controls verified; retired Brevo one-shots return 410.
- Nine backend-only SECURITY DEFINER RPC signatures had `authenticated`/`anon` EXECUTE revoked by live hardening `lock_backend_only_server_rpcs_20260911`; `service_role` retained. Advisor count dropped 33→24.
- Public API surface: 0 public functions executable by anon; 0 public tables/views directly granted to anon/authenticated; 24 intentional authenticated SECURITY DEFINER user RPCs, identity-controlled and fixed-search-path.
- Sensitive special-case/signature/bank/offer/appraisal flows retain role/version/evidence/human gates. Actual bank transport remains blocked with `transport_not_configured`.
- Private document/chat storage contracts verified; chat attachment V2 MIME validation aligned.
- Central document confidence policy V1=0.95; missing policy→`POLICY_CONFLICT`, low confidence→`HUMAN_REQUIRED/LOW_CONFIDENCE` before canonical write.
- Task/stage/document/B2B/notification/profile governance and optimistic-version gates verified.
- ANA canonical knowledge reads only approved/applied/non-test knowledge; candidate decisions remain human-gated.
- All 38 active Edge Functions inventoried; no additional hardcoded secret found in inspected source.
- Six missing FK indexes added additively; advisor now has 0 unindexed foreign-key findings.
- Make hygiene loop: active TEMP/TEST/PRE-PROD scenarios found in the current active inventory were deactivated without deleting configuration/history. Post-change searches return 0 active names matching `TEMP`, `TEST` or `PRE-PROD`. CORE/MASTER/PROD scenarios were preserved.

## EXISTING / intentional architectural warnings
- 40 `fenix_prod` tables: RLS enabled/no policy is an intentional closed-table pattern; no direct anon/authenticated table grants.
- 24 authenticated SECURITY DEFINER warnings are the audited user-facing RPC surface.
- `fenix-reports-api` keeps Dirección company scope and Financiero/Visitador actor scope.

## PARTIAL / pending external or destructive dependency closure
- Make WordPress shared secret remains present in scenarios 9694504 and 9694499. Scenario 9694504 is now inactive as part of PRE-PROD retirement; 9694499 was already inactive. History shows executions only on 2026-08-22 and no retained headers/IP identifying the caller. With both scenarios inactive there is no active Make webhook consumer to preserve, but rotation/removal is still blocked until the external caller/dependency is identified or formally retired. Do not print/commit the value.
- `pg_net` is in `public`, non-relocatable, with extension-owned objects; no Fénix caller found. Drop/recreate blocked pending backup/dependency/restore evidence.
- Supabase Auth leaked-password protection disabled; connector cannot mutate Auth config. No new subscription solely to silence warning.
- Legacy anon and modern publishable keys both active; deployed frontend inventory incomplete, so no blind revocation.
- Auth DB connection allocation absolute-count advisory remains informational.
- Provider restore drill cannot be claimed because current Supabase connector exposes no backup/restore action.
- Legacy `fenix-capital-inmo-map` warnings are predominantly `preprod_test`/`*_preprod`; App PREPROD remains cancelled and untouched.

## Advisor snapshot
Security: 40 intentional RLS INFO; 1 `pg_net` WARN; 24 intentional authenticated SECURITY DEFINER WARN; 1 leaked-password WARN. Performance: unused-index INFO + Auth connection allocation INFO; 0 unindexed FK.

## Rollback
- Make deactivations are reversible by reactivation; scenario configuration/history was not deleted.
- `fenix-web-lead`: redeploy prior Edge version; abuse guard additive.
- Backend RPC hardening: targeted GRANT EXECUTE only on exact former signatures.
- Stage/task/chat validation: restore prior function body if demonstrated regression.
- FK indexes: drop only named additive indexes if demonstrated regression.
- Social lead secret: active credential in Vault; former credential intentionally invalidated.

## Promotion rule
No warning becomes GREEN by documentation alone. GREEN requires live contract/permission/version/test/advisor evidence. External/destructive unknowns remain PARTIAL.
