from pathlib import Path


def test_two_live_callers_block_session_context_retirement_until_migrated():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "fenix-ana-knowledge" in evidence
    assert "fenix-b2b-actions" in evidence
    assert "fenix_prod_session_context()" in evidence
    assert "KEEP_UNTIL_TWO_LIVE_CALLERS_MIGRATED" in evidence
    assert "MUST NOT have `authenticated EXECUTE` revoked yet" in evidence


def test_server_identity_pattern_is_recorded_for_migrated_edge_surfaces():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    for name in ("fenix-directory-actions", "fenix-task-actions", "fenix-expediente-actions"):
        assert name in evidence
    assert "fenix_prod_actor_context_by_auth_server" in evidence


def test_caller_map_does_not_authorize_bulk_retirement():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "no bulk revoke" in evidence.lower()
    assert "No function ACL" in evidence
