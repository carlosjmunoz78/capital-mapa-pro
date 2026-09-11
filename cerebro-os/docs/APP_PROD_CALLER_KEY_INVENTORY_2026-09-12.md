# CEREBRO OS · APP PROD caller/key inventory · 2026-09-12

## Scope
Read-only mapping of the currently deployed APP source contract (`carlosjmunoz78/fenix-capital-inmo-map`, default branch `main`) to Supabase PROD. No App/CRM behavior changed. App PREPROD remains cancelled.

## CONFIRMED from current `main`
- PROD project URL used by the frontend: `https://cluhljgonannaafpmblx.supabase.co`.
- Frontend runtime uses `VITE_SUPABASE_PUBLISHABLE_KEY`; the canonical production example names only the modern publishable-key variable, not a legacy anon variable.
- `src/supabase.ts` contains a production fallback publishable key and the PROD project URL. A publishable frontend key is deliberately browser-visible; it must not be confused with `service_role` or another secret credential.
- The production deploy workflow also injects the same modern publishable key and asserts the bundle contains PROD and not the retired App PREPROD project URL.
- PROD auth storage namespace is `fenix-prod-auth-v1`; PREPROD namespace remains separate and is not reactivated.

## Confirmed frontend Edge callers
`src/supabase.ts` routes authenticated browser calls through these production Edge Functions (no `-test` suffix in PROD):

- `fenix-app-gateway`
- `fenix-ana-api`
- `fenix-ana-knowledge`
- `fenix-ana-canonical`
- `fenix-evidence-api`
- `fenix-memory-api`
- `fenix-b2b-actions`

The shared browser call contract sends the signed-in user's access token as `Authorization: Bearer ...` and the modern publishable key as `apikey`.

## Additional PROD smoke callers
The current `prod-runtime-smoke.yml` exercises:

- `fenix-app-gateway/health`
- `fenix-app-gateway/session/context`
- `fenix-directory-api/notarias`
- `fenix-directory-api/registros-propiedad`
- `fenix-economia-api/economia`
- `fenix-reports-api/reports`
- retired one-shot functions: `fenix-directory-sync-once`, `fenix-directory-sync-trigger-once`, `fenix-crm-sync-once`, `fenix-crm-sync-trigger-once`, `fenix-prod-data-sync-once`, `fenix-legacy-doc-migration-once`
- `fenix-ana-api/capabilities` CORS preflight
- `fenix-ana-knowledge/recent`

## Legacy anon dependency found
The production runtime smoke workflow still contains a legacy Supabase anon JWT solely for the `fenix-ana-knowledge/recent` configuration probe. It is used as anonymous JWT/API-key material to reach the function far enough to distinguish missing server configuration from the expected identity failure.

This means legacy anon-key rotation/revocation is **NOT yet safe** even though the browser application's normal runtime uses the modern publishable key. The live dependency is CI/smoke, not the normal frontend client path identified above.

Do not paste the legacy JWT into CEREBRO Registry or documentation. Its concrete value already exists in the App repository workflow and is intentionally omitted here.

## Security interpretation
- Modern Supabase publishable keys are public client identifiers/credentials intended for browser use; their presence in frontend code is not equivalent to exposing `service_role`.
- No evidence in this audit supports revoking the legacy anon key blindly because the production smoke test still depends on it.
- No evidence in this audit supports changing App runtime auth/RBAC merely to remove the smoke dependency.

## Required closure before legacy anon rotation
1. Replace the smoke-only legacy-anon probe with a supported health/config check that does not require the legacy anon JWT, while preserving fail-closed identity behavior.
2. Run the production smoke against the replacement contract and obtain GREEN evidence.
3. Search deployed workflows/runtime consumers again for legacy anon use.
4. Only then rotate/revoke the legacy anon credential through the provider-supported path.
5. Rerun APP domain, gateway, CORS, identity and Edge smoke checks.
6. Preserve rollback until the post-rotation smoke is GREEN.

## State
- APP normal runtime → modern publishable key: **HECHO / VERIFIED BY SOURCE CONTRACT**.
- APP Edge caller map above: **HECHO / VERIFIED BY SOURCE CONTRACT**.
- Legacy anon dependency identification: **HECHO** (production runtime smoke workflow).
- Legacy anon removal/rotation: **PARCIAL / BLOCKED UNTIL REPLACEMENT PROBE + PROVIDER ROTATION PATH**.
- App PREPROD: **CANCELLED; NOT REACTIVATED**.
