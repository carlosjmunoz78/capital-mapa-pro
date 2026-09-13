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
- Merge commit now on `main`: `dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c`.
- PROD Live Deploy run `34790008072` completed SUCCESS for that exact merge commit.
- The deploy job built canonical PROD, asserted no PRE-PROD backend, prepared the static live branch and published the canonical snapshot successfully.
- `gh-pages` deployment commit `c8a4bc720ce91eb46ed811c506623c265d043594` records `deploy: PROD live snapshot dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c`.
- `gh-pages/PROD_SOURCE_SHA.txt` contains exactly `dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c`.
- Default-branch code search after merge returns no occurrence for the previously evidenced direct caller `fenix_prod_contact_create_v2` and no generic `rpc( fenix_prod` match.
- PREPROD App remains cancelled; no PREPROD reactivation is claimed.

### Parallel hosting evidence

The same merge SHA also triggered connected Cloudflare checks. Two Workers production builds completed SUCCESS (`fenix-capital-inmo-map` and `fenix-capital-inmo-maps`). A separate legacy/parallel `Cloudflare Pages` check failed immediately for the same SHA. This failure is not silently classified as harmless: its active routing role is not proven from the available connector, so it remains a hosting-topology item to audit before deleting or disabling any Cloudflare integration.

## Live Supabase security evidence

Project scope: Fénix primary PROD project. Project identifier intentionally not repeated here.

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

### Null actor hardening

Migration applied: `harden_server_wrappers_null_actor_guard_20260914`.

The migration corrected SQL NULL semantics in:

- `fenix_prod_exp_create_server`
- `fenix_prod_sign_create_server`

Both now explicitly deny when `v_role IS NULL` before evaluating allowed roles. Post-migration probes returned `403` for nonexistent actors while preserving server-only grants.

## Controlled Gateway routing

- `fenix-app-gateway` live version after controlled deployment: `v17`.
- Existing custom authentication pattern was preserved: Bearer token -> user validation -> actor context -> service-role server wrapper.
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

This proves live database/RPC parity for the five target wrapper families. It still does **not** substitute for authenticated browser-to-Edge HTTP E2E.

## APP-007 Communications

- Live `fenix-communications-gateway` exists at `v8`, JWT verification enabled.
- Current promoted `CommunicationsShell` targets the PROD communications gateway and its prepare/send contract aligns with the live gateway.
- It still references `fenix-expediente-assistant-test` for optional advice.
- No equivalent advice endpoint was evidenced in the inspected current Edge inventory.
- Advice failure is fail-soft.
- No real communication was sent for verification.

## APP-009 / APP-010 CEREBRO Console

- Internal App route `/cerebro` is now part of the promoted source commit.
- Profile launcher remains guarded.
- Console URL configuration accepts explicit HTTPS only and fails closed when absent.
- Logical Console flow remains `CONSOLE -> GATEWAY -> POLICY -> ENGINE -> AUDIT`.
- No deployed authenticated CEREBRO Console Gateway URL is evidenced yet.
- No external live Console Gateway is claimed.

## Credential Registry

- Metadata-only credential registry is present in CEREBRO.
- Raw password/token/API-key/secret fields are rejected by validation.
- Provider-managed opaque credentials and vault references are supported.
- No raw credential value is recorded in this evidence.

## Current gates / not green yet

1. Obtain authenticated HTTP E2E evidence through `fenix-app-gateway` using a real, safe authenticated user context.
2. Prove rollback/non-durable cleanup for the complete HTTP write path before privilege retirement.
3. Only after HTTP E2E + rollback: capture final caller-retirement evidence and selectively retire legacy `authenticated EXECUTE`; never bulk-revoke managed/system functions.
4. Resolve the connected Cloudflare topology enough to classify the failing Pages check without deleting a possibly active legacy route.
5. Resolve or formally retire/replace the missing APP-007 optional advice dependency.
6. Deploy and authenticate the real CEREBRO Console Gateway before enabling any external profile link.
7. Continue closure order: Security -> Recovery -> Observability -> FinOps -> final human-gated Promotion.

## CEREBRO branch evidence

- Repository: `carlosjmunoz78/capital-mapa-pro`
- Branch: `cerebro-engine-factory-v0`
- Factory/recovery/observability CI is green in the previously captured runs.
- This evidence update records the newly completed real App promotion while keeping unproven HTTP/hosting claims fail-closed.

## Policy conclusion

The reviewed RPC migration is no longer merely branch-ready: PR #376 has been promoted to `main`, the canonical PROD deployment workflow succeeded, and the `gh-pages` snapshot provenance points to the exact merge SHA. Source-level live caller retirement therefore materially advanced to green. Global Security remains `PARTIAL` until authenticated HTTP E2E/rollback is proven and only then can legacy authenticated EXECUTE be retired selectively. No destructive privilege change was made from deployment evidence alone.
