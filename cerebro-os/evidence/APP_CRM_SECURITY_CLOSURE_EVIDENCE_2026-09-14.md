# CEREBRO OS · APP/CRM Security Closure Evidence · 2026-09-14

## Scope

Evidence-only checkpoint for the authorized APP/CRM RPC migration and Security closure loop. This file contains no credentials, tokens, customer data or secret values.

## APP migration and promotion evidence

- Repository: `carlosjmunoz78/fenix-capital-inmo-map`
- Migration branch: `cerebro-app-crm-rpc-migration-v0-20260913`
- Reviewed branch HEAD: `b1b6fb5404a4704c5d637fc770fc90e9f2eb8312`
- Pull request: `#376` toward `main`
- Dedicated branch audit CI: run `34786441006`, job `audit-and-build` SUCCESS
- Persisted direct PROD RPC callers in the reviewed branch: `0`
- PR #376 was marked ready and merged only after the explicit human promotion authorization in the closure loop.
- Merge commit on `main`: `dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c`.
- PROD Live Deploy run `34790008072` completed SUCCESS for that exact merge commit.
- `gh-pages` deployment commit `c8a4bc720ce91eb46ed811c506623c265d043594` records the canonical PROD snapshot for that migration.
- Default-branch code search after merge returns no occurrence for the previously evidenced direct caller `fenix_prod_contact_create_v2` and no generic `rpc( fenix_prod` match.
- PREPROD App remains cancelled; no PREPROD reactivation is claimed.

### Parallel hosting evidence

GitHub Pages remains the canonical static PROD path. Cloudflare remains a parallel/legacy topology item and must not be disabled or deleted without routing evidence and rollback.

## Live Supabase security evidence

- `fenix_prod` physical tables: `44`
- RLS enabled: `44/44`
- Five target server-only wrappers are present:
  - `fenix_prod_notifications_list_server`
  - `fenix_prod_notification_mark_server`
  - `fenix_prod_contact_create_server`
  - `fenix_prod_exp_create_server`
  - `fenix_prod_sign_create_server`
- All five are `SECURITY DEFINER` with explicit `search_path`.
- `anon EXECUTE = false` for all five.
- `authenticated EXECUTE = false` for all five.
- `service_role EXECUTE = true` for all five.
- Unknown-actor probes return fail-closed `403` for all five.

Current Supabase advisor snapshot remains controlled:
- `44` RLS-with-no-policy informational findings, intentional fail-closed in this architecture;
- `24` authenticated `SECURITY DEFINER` warnings under selective review;
- `pg_net` in `public` remains untouched;
- leaked-password protection remains disabled and requires a supported configuration channel / policy decision.

No bulk revoke, extension move/recreate or index deletion has been performed.

## Controlled Gateway routing

- `fenix-app-gateway` live version: `v17`.
- Existing custom authentication pattern is preserved: Bearer token -> user validation -> actor context -> service-role server wrapper.
- Required target routes are present live:
  - `POST /expedientes`
  - `PATCH /expedientes/:code`
  - `POST /contactos`
  - `POST /firmas`
  - `GET/POST /chat`
  - `GET /notificaciones`
  - `POST /notificaciones/:id/state`
- No legacy authenticated RPC privilege has been revoked merely from source/deploy evidence.

## OLD vs NEW parity evidence

A rollback-safe transaction in live PROD executed semantic OLD vs NEW comparisons with a valid linked Dirección actor and then issued `ROLLBACK`. The probe generated no persistent test contact, expediente, firma or notification-state mutation.

| Contract | OLD | NEW | Result |
|---|---:|---:|---|
| notifications list | 200 | 200 | parity |
| notification mark | 200 | 200 | parity |
| contact create | 201 | 201 | parity |
| expediente create | 201 | 201 | parity |
| firma create | 201 | 201 | parity |

This proves live database/RPC parity for the five target wrapper families. It does not substitute for authenticated browser-to-Edge write E2E.

## Authenticated HTTP E2E

Permanent operational identity `CEREBRO-OPS-01` is linked and authenticated successfully in the live Fénix App. Human browser evidence proves the authenticated notifications read path.

The four durable write paths remain **BLOCKED_FAIL_CLOSED** because the live gateway exposes no proven cleanup route for test mutations. The operational identity is permanent and must not be deleted/retired as a cleanup mechanism.

Therefore no durable contact, expediente, firma or notification-state write is executed merely to obtain a green test badge.

## Legacy RPC retirement

Prepared-but-not-applied retirement SQL exists at:
`cerebro-os/security/APP_LEGACY_RPC_RETIREMENT_PREPARED_NOT_APPLIED_2026-09-14.sql`.

All eight target legacy RPC names have returned zero indexed callers in current App source searches; GitHub reports those searches as incomplete, so this is supporting evidence, not proof of universal caller absence.

Retirement remains gated by authenticated HTTP write E2E + cleanup/rollback evidence. No premature `REVOKE` has been applied.

## APP-007 Communications

- Live `fenix-communications-gateway` exists at `v8`, JWT verification enabled.
- Current promoted `CommunicationsShell` targets the PROD communications gateway and its prepare/send contract aligns with the live gateway.
- No real communication was sent for verification.

## APP-009 / APP-010 CEREBRO Console

State: **GREEN for authenticated read-only Console V0 transport**.

- `/cerebro` is live in PROD.
- `cerebro-console-gateway-v0` is deployed as an authenticated read-only surface.
- Live browser evidence showed `Transporte autenticado verificado`.
- PR #378 isolated the Console visual surface from the ordinary App shell and contextual Ana overlay.
- Merge commit: `07b8df2774997f46a9c1136c47256d9f51edeaa8`.
- PROD Live Deploy run `34827325954` completed successfully and published the corrected snapshot to `gh-pages`.
- Chat, commands, autonomous PROD execution and live writes remain disabled by design.
- No direct model access is enabled.

## Recovery

- App source-release rollback rehearsal: **GREEN**.
- Provider-level database restore: **HUMAN_REQUIRED(MONEY_LIMIT)**.
- Live read-only Supabase branch inventory contains only default `main`; no isolated restore target is currently available for a safe provider restore drill.
- Restore onto PROD is prohibited.

See `APP_PROD_ROLLBACK_REHEARSAL_C7A15C_2026-09-14.md` and `RECOVERY_PROVIDER_DB_RESTORE_GATE_2026-09-14.md`.

## Observability

- Persistent zero-additional-cost Google Sheets sink exists and has been independently proven.
- Latest controlled retest succeeded and inserted row `3` through Make scenario `9804649`.
- Base sink infrastructure: **GREEN**.
- Production-wide wiring of all engines: **PARCIAL**, to be introduced in parallel by engine/family rather than replacing existing observability.

## FinOps

- Current cost evidence is recorded separately without mixing EUR and USD.
- Notion has real API/data dependencies through active Make scenarios.
- No shared Notion Agents were found at audit time.
- The current higher-cost Notion plan is a strong downgrade candidate, but any billing change remains `HUMAN_REQUIRED(MONEY_LIMIT)` until Business-only dependency checks are complete.

See `FINOPS_CURRENT_COST_AND_NOTION_DEPENDENCY_2026-09-14.md`.

## YouTube

State: **GREEN**.

The health scenario is active after supported OAuth reauthorization. Post-repair automatic executions completed successfully with three operations each and no video modification.

## Current gates / not green yet

1. Prove a non-durable or cleanup-safe authenticated HTTP E2E strategy for the four write routes.
2. Only after that evidence, selectively retire the eight legacy authenticated RPC signatures; never bulk-revoke managed/system functions.
3. Provider DB restore remains `MONEY_LIMIT` until an approved isolated restore target exists.
4. Wire the persistent observability sink to PROD engines incrementally with OLD vs NEW comparison and rollback.
5. Finish Notion Business-only dependency audit before any downgrade action.
6. Keep Cloudflare parallel topology untouched until its dependency/routing role is fully classified.

## Policy conclusion

App migration, source promotion, Gateway routing, source rollback, YouTube health, Console V0 authenticated read-only transport and persistent observability base are evidenced green. The remaining red/partial items are intentionally fail-closed gates rather than reasons to bypass policy: durable write cleanup, selective legacy RPC retirement, provider DB restore cost and production-wide observability wiring. No destructive privilege, billing or provider-restore action has been taken without the required gate.
