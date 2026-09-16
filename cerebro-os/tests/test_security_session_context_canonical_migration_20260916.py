from pathlib import Path


def test_canonical_caller_migration_is_recorded_with_rollback():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_CANONICAL_MIGRATION_20260916.md").read_text()
    assert "fenix-ana-canonical" in evidence
    assert "version: `10`" in evidence
    assert "dc9c251a248c0151efbfe87f3a53b072c6650ea97592e5825c493d6ea999d5da" in evidence
    assert "fenix-ana-canonical-v9.ts" in evidence
    assert "fenix_prod_actor_context_by_auth_server" in evidence


def test_session_context_acl_retirement_stays_blocked_after_one_more_migration():
    evidence = Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_CANONICAL_MIGRATION_20260916.md").read_text()
    for caller in ("fenix-memory-api", "fenix-evidence-api", "fenix-ana-api"):
        assert caller in evidence
    assert "MUST NOT be revoked yet" in evidence
    assert "POR_AUDITAR" in evidence
    assert "does not grant SECURITY green" in evidence
