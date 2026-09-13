# CEREBRO OS · APP/CRM Security Closure Evidence · 2026-09-14

## Scope

Evidence-only checkpoint for the authorized APP/CRM RPC migration and Security closure loop. This file contains no credentials, tokens, customer data or secret values.

## APP branch evidence

- Repository: `carlosjmunoz78/fenix-capital-inmo-map`
- Branch: `cerebro-app-crm-rpc-migration-v0-20260913`
- Verified HEAD: `b1b6fb5404a4704c5d637fc770fc90e9f2eb8312`
- Pull request: `#376` toward `main`
- Reference main at verification: `95106d8e792257f809033486b7025d81665ea83b`
- Dedicated audit CI: run `34786441006`, job `audit-and-build` SUCCESS
- Persisted direct PROD RPC callers in the branch: `0`
- PREPROD App remains cancelled; no PREPROD reactivation is claimed.
- Main/PROD App deployment is not claimed by this evidence.

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
  - `POST /contactos`
  - `POST /firmas`
  - `GET /notificaciones`
  - `POST /notificaciones/:id/state`
- No legacy authenticated RPC privilege was revoked.

## OLD vs NEW parity evidence

A rollback-safe transaction in live PROD executed semantic OLD vs NEW comparisons with a valid linked Dirección actor and then issued `ROLLBACK`. The probe generated no persistent test contact, expediente, firma or notification-state mutation.

Parity results:

| Contract | OLD | NEW | Result |
|---|---:|---:|---|
| notifications list | 200 | 200 | parity |
| notification mark | 200 | 200 | parity |
| contact create | 201 | 201 | parity |
| expediente create | 201 | 201 | parity |
| firma create | 201 | 201 | parity |

This proves live database/RPC parity for the five target wrapper families. It does **not** prove authenticated browser-to-Edge HTTP E2E and does **not** prove that the currently deployed App has zero direct legacy callers.

## APP-007 Communications

- Live `fenix-communications-gateway` exists at `v8`, JWT verification enabled.
- Branch `CommunicationsShell` targets the PROD communications gateway and its prepare/send contract aligns with the live gateway.
- The branch still references `fenix-expediente-assistant-test` for optional advice.
- No equivalent advice endpoint was evidenced in the inspected current Edge inventory.
- Advice failure is fail-soft in the branch.
- No real communication was sent for verification.

## APP-009 / APP-010 CEREBRO Console

- Internal App route `/cerebro` exists in the migration branch.
- Profile launcher is guarded.
- Console URL configuration accepts explicit HTTPS only and fails closed when absent.
- Logical Console flow remains `CONSOLE -> GATEWAY -> POLICY -> ENGINE -> AUDIT`.
- No deployed authenticated CEREBRO Console Gateway URL is evidenced yet.
- No live profile launcher is claimed.

## Credential Registry

- Metadata-only credential registry is present in CEREBRO.
- Raw password/token/API-key/secret fields are rejected by validation.
- Provider-managed opaque credentials and vault references are supported.
- No raw credential value is recorded in this evidence.

## Current gates / not green yet

1. Prove zero direct legacy RPC callers in the **currently deployed live App**, not only in the branch.
2. Prove authenticated HTTP E2E through `fenix-app-gateway` for the target routes without creating durable test records.
3. Prove rollback for the complete HTTP write path.
4. Do not revoke legacy `authenticated EXECUTE` until live caller retirement and HTTP parity are evidenced.
5. Resolve or formally retire/replace the missing APP-007 advice dependency.
6. Deploy and authenticate the real CEREBRO Console Gateway before enabling the profile link.
7. Continue closure order: Security -> Recovery -> Observability -> FinOps -> final human-gated Promotion.

## CEREBRO branch evidence

- Repository: `carlosjmunoz78/capital-mapa-pro`
- Branch: `cerebro-engine-factory-v0`
- Console readiness mismatch was repaired and CI returned success.
- Closure matrices were updated to reflect live wrapper/routing/parity evidence while remaining fail-closed for unproven live-App/HTTP/Console claims.

## Policy conclusion

The five target wrapper families and controlled Gateway routing have materially advanced and live RPC parity is demonstrated. Global Security and APP/CRM promotion remain `PARTIAL` until live deployed App caller retirement and authenticated HTTP E2E/rollback are proven. Legacy privileges remain untouched.
