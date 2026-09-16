from pathlib import Path


def test_live_ana_knowledge_blocks_session_context_retirement_until_migrated():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "fenix-ana-knowledge" in evidence
    assert "fenix_prod_session_context()" in evidence
    assert "KEEP_UNTIL_LIVE_CALLER_MIGRATED" in evidence
    assert "MUST NOT have `authenticated EXECUTE` revoked yet" in evidence


def test_caller_map_does_not_authorize_bulk_retirement():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()
    assert "no bulk revoke" in evidence.lower()
    assert "No function ACL" in evidence
