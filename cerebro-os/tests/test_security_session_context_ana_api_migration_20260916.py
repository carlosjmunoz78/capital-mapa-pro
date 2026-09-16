from pathlib import Path


def test_ana_api_migration_has_live_and_rollback_evidence():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_ANA_API_MIGRATION_20260916.md").read_text()
    assert "fenix-ana-api" in evidence
    assert "version: `11`" in evidence
    assert "b657f7336fb7baac4fce236f2158c778ccd896a742c87d378ece44c744ce0cc5" in evidence
    assert "fenix-ana-api-v10.ts" in evidence
    assert "fenix_prod_actor_context_by_auth_server" in evidence


def test_session_context_retirement_remains_blocked_by_two_known_callers():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_ANA_API_MIGRATION_20260916.md").read_text()
    assert "fenix-memory-api" in evidence
    assert "fenix-evidence-api" in evidence
    assert "MUST NOT be revoked yet" in evidence
    assert "POR_AUDITAR" in evidence
    assert "does not grant SECURITY green" in evidence
