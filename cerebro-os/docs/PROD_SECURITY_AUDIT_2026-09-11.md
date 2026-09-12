# CEREBRO OS · PROD security/performance audit · 2026-09-11

## Scope
Evidence-first PROD audit. Remediation only when reversible and contract-preserving. App/CRM functional behavior preserved. No raw secret committed.

## GREEN / remediated
- `social-lead-ingest` v5: former hardcoded shared secret removed; Supabase-side verifier remains Vault-backed; live Make scenario 9768402 module 8 now uses provider-managed API-key authentication through opaque keychain 217038 and no literal `x-fenix-key` header remains in the module mapper.
- The Make secure-credential authorization request `efdac03c-20c0-4cba-af14-1e33714461bd` is authorized. Its returned connection id 217036 is retained as an authorized-but-unused opaque credential; the live module currently references 217038. Neither credential value is stored in Git.
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
- Make hygiene loop: active TEMP/TEST/PRE-PROD scenarios found in the active inventory were deactivated without deleting configuration/history. Post-change searches return 0 active names matching `TEMP`, `TEST` or `PRE-PROD`. CORE/MASTER/PROD scenarios were preserved.
- PRE-PROD Make inventory re-audited live on 2026-09-12: exactly three matching scenarios were found and all are inactive. 9694039 is a read-only GSC/GA4 bridge with healthy provider connections and zero queued webhook deliveries. 9694504 and 9694499 remain inactive, their former shared-secret gate is replaced by the fail-closed sentinel `__DISABLED_LEGACY_PREPROD__`, and both have zero queued webhook deliveries.
- Inactive TEST WordPress mutators 9694471 and 9556936 plus TEST clone/readback 9694633 were re-audited live: all remain inactive/on-demand, retain provider-managed WordPress connection 14438797, and were not reactivated or executed.
- Archival/error LinkedIn duplicates 5565247 and 5566037 are explicitly marked `NO USAR`, remain in Make `error` state, have zero incomplete executions, and their descriptions identify the replacement scenarios. They are retained for traceability rather than repaired into runnable duplicates.
- 2026-09-12 live advisor rerun confirms the same security shape: 40 intentional RLS-no-policy INFO, 1 `pg_net` WARN, 24 authenticated SECURITY DEFINER WARN, 1 leaked-password WARN. Performance still has no unindexed-FK warning; remaining notices are unused-index INFO plus Auth absolute connection allocation INFO.
- 2026-09-12 `pg_net` dependency recheck: extension is still in `public`, `extrelocatable=false`, owns 28 extension objects. No Fénix trigger definition references `net.*`; no `cron` schema exists. The only non-extension function body matching `net.*` is Supabase helper `extensions.grant_pg_net_access`, so no application caller was identified by database-side dependency scan.

## EXISTING / intentional architectural warnings
- 40 `fenix_prod` tables: RLS enabled/no policy is an intentional closed-table pattern; no direct anon/authenticated table grants.
- 24 authenticated SECURITY DEFINER warnings are the audited user-facing RPC surface.
- `fenix-reports-api` keeps Dirección company scope and Financiero/Visitador actor scope.
- Inactive historical TEST/TEMP/ERROR Make scenarios are preserved as historical/audit artifacts when they are not active consumers. Inactive does not mean promoted or production-ready.

## PARTIAL / pending external or destructive dependency closure
- `social-lead-ingest` Make configuration remediation is GREEN, but runtime authentication after the keychain migration remains `PARTIAL_RUNTIME_EVIDENCE`: no successful scenario execution exists after the migration timestamp. A synthetic non-duplicate run would create/update APP/CRM PROD data, so it must not be manufactured merely to obtain a green checkmark.
- The full inactive TEST/TEMP Make inventory remains `IN_PROGRESS`: Make returns at most 25 scenarios per query, so the inventory is being closed by narrowed searches/subsets. Audited inactive scenarios remain quarantined; none are reactivated solely for testing.
- `pg_net` is in `public`, non-relocatable, with 28 extension-owned objects. Database-side caller scan found no Fénix trigger/function/cron caller, but drop/recreate remains blocked pending a verified backup/restore path because removal is destructive and `extrelocatable=false`.
- Supabase Auth leaked-password protection disabled; connector cannot mutate Auth config. No new subscription solely to silence warning.
- Legacy anon and modern publishable keys both active; deployed frontend inventory incomplete, so no blind revocation.
- Auth DB connection allocation absolute-count advisory remains informational.
- Provider restore drill cannot be claimed because current Supabase connector exposes no backup/restore action.
- Legacy `fenix-capital-inmo-map` warnings are predominantly `preprod_test`/`*_preprod`; App PREPROD remains cancelled and untouched.

## Advisor snapshot
Security: 40 intentional RLS INFO; 1 `pg_net` WARN; 24 intentional authenticated SECURITY DEFINER WARN; 1 leaked-password WARN. Performance: unused-index INFO + Auth connection allocation INFO; 0 unindexed FK.

## Rollback
- Make deactivations are reversible by reactivation; scenario configuration/history was not deleted.
- Make provider-managed credential migration: preserve the current module blueprint and opaque keychain reference; do not restore a literal header secret. Any credential switch requires dependency/runtime verification.
- `fenix-web-lead`: redeploy prior Edge version; abuse guard additive.
- Backend RPC hardening: targeted GRANT EXECUTE only on exact former signatures.
- Stage/task/chat validation: restore prior function body if demonstrated regression.
- FK indexes: drop only named additive indexes if demonstrated regression.
- Social lead secret: active credential remains provider-managed/Vault-backed; raw value is never committed.

## `pg_net` controlled-removal gate
Do not execute destructive removal until all gates are evidenced:
1. provider/database backup reference captured;
2. dependency snapshot stored;
3. SQL/object export sufficient to rebuild extension-adjacent state;
4. restore/rebuild drill executed outside PROD;
5. extension reinstall path verified for the exact Supabase/Postgres environment;
6. OLD vs NEW smoke confirms App/CRM/Edge behavior unchanged;
7. rollback/reinstall procedure timed and documented.
Until then the correct state is `PARTIAL_CONTROLLED`, not RED-by-force and not GREEN-by-prose.

## Promotion rule
No warning becomes GREEN by documentation alone. GREEN requires live contract/permission/version/test/advisor evidence. External/destructive unknowns remain PARTIAL.
