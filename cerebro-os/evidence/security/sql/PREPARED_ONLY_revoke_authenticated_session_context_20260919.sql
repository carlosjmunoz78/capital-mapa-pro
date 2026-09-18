-- PREPARED ONLY. DO NOT APPLY WITHOUT EXACT AUTHORIZATION:
-- AUTORIZO RETIRO SELECTIVO RPC PROD
--
-- Scope: revoke authenticated EXECUTE from the legacy user-facing
-- public.fenix_prod_session_context() function only.
--
-- Preconditions:
-- 1) zero known ACTIVE Edge direct callers;
-- 2) live ACL/definition snapshot captured immediately before apply;
-- 3) rollback grant available;
-- 4) no other function privileges changed.

REVOKE EXECUTE ON FUNCTION public.fenix_prod_session_context() FROM authenticated;
