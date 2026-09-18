-- ROLLBACK for selective session_context retirement.
-- Apply if post-change verification or authenticated-path E2E fails.

GRANT EXECUTE ON FUNCTION public.fenix_prod_session_context() TO authenticated;
