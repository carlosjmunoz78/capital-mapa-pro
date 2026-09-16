from pathlib import Path


def test_known_session_context_callers_are_migrated_but_acl_retirement_stays_blocked():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "fenix-ana-knowledge` v10 · MIGRATED IN PROD" in evidence
    assert "fenix-b2b-actions` v10 · MIGRATED IN PROD" in evidence
    assert "MIGRATED_KNOWN_EDGE_CALLERS_ACL_RETIREMENT_STILL_BLOCKED" in evidence
    assert "authenticated HTTP E2E" in evidence
    assert "POR_AUDITAR" in evidence
    assert "MUST NOT be revoked yet" in evidence


def test_server_identity_pattern_is_recorded_for_migrated_edge_surfaces():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    for name in ("fenix-directory-actions", "fenix-task-actions", "fenix-expediente-actions"):
        assert name in evidence
    assert "fenix_prod_actor_context_by_auth_server" in evidence


def test_caller_map_does_not_authorize_bulk_retirement_or_global_green():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "No bulk revoke" in evidence or "no bulk revoke" in evidence
    assert "do not grant SECURITY green" in evidence
    assert "16 `authenticated_security_definer_function_executable`" in evidence
