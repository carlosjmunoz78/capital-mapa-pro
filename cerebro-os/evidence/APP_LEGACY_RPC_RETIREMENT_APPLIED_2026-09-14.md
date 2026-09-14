# CEREBRO OS · APP legacy RPC retirement · APPLIED · 2026-09-14

## HECHO

The previously prepared retirement batch was executed manually in Supabase SQL Editor after authenticated PROD E2E and cleanup gates were confirmed.

Retired from `authenticated`:

1. `fenix_prod_chat_list_user(integer)`
2. `fenix_prod_chat_send_user(text,text)`
3. `fenix_prod_contact_create(text,text,text,text,text,text,text,text,boolean)`
4. `fenix_prod_exp_create(text,text,text,text,text,numeric,numeric,text,text,jsonb,boolean)`
5. `fenix_prod_exp_update(text,integer,text,text,text,text,date)`
6. `fenix_prod_notifications_list_user(integer)`
7. `fenix_prod_notification_mark_user(uuid,text)`
8. `fenix_prod_sign_create(text,timestamptz,text,text,timestamptz,timestamptz,date)`

Human execution result: `Success. No rows returned`.

## POST-APPLY VERIFICATION

Supabase Security Advisor after application reports `authenticated_security_definer_function_executable = 16`, down from the prior 24. This is exactly an 8-function reduction, matching the intended retirement scope.

Direct privilege verification confirmed:

- all eight retired RPCs: `authenticated EXECUTE = false`
- all eight retired RPCs: `service_role EXECUTE = true`
- target server wrappers remain `authenticated EXECUTE = false`
- target server wrappers remain `service_role EXECUTE = true`

Verified server wrappers:

- `fenix_prod_notifications_list_server`
- `fenix_prod_notification_mark_server`
- `fenix_prod_contact_create_server`
- `fenix_prod_exp_create_server`
- `fenix_prod_sign_create_server`

## PRECEDING GATES

Before retirement, authenticated PROD HTTP E2E was completed through `fenix-app-gateway` using the permanent operational identity, with these HTTP results:

- notification write: 200
- contact create: 201
- expediente create: 201
- firma create: 201

Immediate cleanup was then executed and the user confirmed all four final residue counters were zero.

## REMAINING SECURITY ADVISORIES

The current advisor still reports:

- 44 `rls_enabled_no_policy` INFO findings, intentionally fail-closed under the current gateway/server-wrapper architecture;
- 16 remaining authenticated SECURITY DEFINER functions requiring separate disposition, not bulk revocation;
- `pg_net` in `public`; do not move/drop/recreate blindly;
- leaked-password protection disabled; this remains a separate account/configuration item.

## ROLLBACK

Rollback remains the inverse `GRANT EXECUTE ... TO authenticated` batch recorded in `cerebro-os/security/APP_LEGACY_RPC_RETIREMENT_PREPARED_NOT_APPLIED_2026-09-14.sql`.

## STATUS

Legacy APP compatibility RPC retirement gate: **GREEN / APPLIED / VERIFIED**.

This does not declare all Supabase security advisories green. The remaining 16 SECURITY DEFINER functions must be handled by their own preserve/wrap/retire decisions.