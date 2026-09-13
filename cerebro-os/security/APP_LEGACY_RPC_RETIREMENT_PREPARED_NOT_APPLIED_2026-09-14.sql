-- CEREBRO OS · APP legacy RPC retirement
-- PREPARED ONLY / NOT APPLIED
-- Date: 2026-09-14
-- Gate: do not execute until authenticated HTTP E2E + write-path rollback are GREEN.
-- Scope deliberately limited to the eight compatibility RPCs migrated behind fenix-app-gateway.
-- The corresponding *_server functions remain service_role-only and are not changed here.

begin;

revoke execute on function public.fenix_prod_chat_list_user(integer) from authenticated;
revoke execute on function public.fenix_prod_chat_send_user(text,text) from authenticated;
revoke execute on function public.fenix_prod_contact_create(text,text,text,text,text,text,text,text,boolean) from authenticated;
revoke execute on function public.fenix_prod_exp_create(text,text,text,text,text,numeric,numeric,text,text,jsonb,boolean) from authenticated;
revoke execute on function public.fenix_prod_exp_update(text,integer,text,text,text,text,date) from authenticated;
revoke execute on function public.fenix_prod_notifications_list_user(integer) from authenticated;
revoke execute on function public.fenix_prod_notification_mark_user(uuid,text) from authenticated;
revoke execute on function public.fenix_prod_sign_create(text,timestamptz,text,text,timestamptz,timestamptz,date) from authenticated;

commit;

-- ROLLBACK (execute only if rollback gate fires):
-- begin;
-- grant execute on function public.fenix_prod_chat_list_user(integer) to authenticated;
-- grant execute on function public.fenix_prod_chat_send_user(text,text) to authenticated;
-- grant execute on function public.fenix_prod_contact_create(text,text,text,text,text,text,text,text,boolean) to authenticated;
-- grant execute on function public.fenix_prod_exp_create(text,text,text,text,text,numeric,numeric,text,text,jsonb,boolean) to authenticated;
-- grant execute on function public.fenix_prod_exp_update(text,integer,text,text,text,text,date) to authenticated;
-- grant execute on function public.fenix_prod_notifications_list_user(integer) to authenticated;
-- grant execute on function public.fenix_prod_notification_mark_user(uuid,text) to authenticated;
-- grant execute on function public.fenix_prod_sign_create(text,timestamptz,text,text,timestamptz,timestamptz,date) to authenticated;
-- commit;

-- Mandatory post-apply evidence before declaring Security GREEN:
-- 1. Supabase advisor count drops only for the intended eight RPCs.
-- 2. service_role EXECUTE on the server wrappers remains true.
-- 3. authenticated HTTP E2E through fenix-app-gateway still succeeds.
-- 4. live App source SHA remains the approved deployment.
-- 5. rollback commands have been validated syntactically in a non-mutating rehearsal.
