from pathlib import Path


def test_ana_migration_removes_direct_authenticated_session_context_rpc():
    source = Path("cerebro-os/security/edge-functions/fenix-ana-knowledge/index.ts").read_text()
    assert "rpc('fenix_prod_session_context')" not in source
    assert "SUPABASE_SERVICE_ROLE_KEY" in source
    assert "auth.auth.getUser" in source
    assert "fenix_prod_actor_context_by_auth_server" in source
    assert "p_auth_user_id:ud.user.id" in source


def test_ana_rollback_snapshot_preserved():
    snapshot = Path("cerebro-os/evidence/security/edge-function-snapshots/fenix-ana-knowledge-v9.ts").read_text()
    assert "rpc('fenix_prod_session_context')" in snapshot
    assert "SUPABASE_SERVICE_ROLE_KEY" not in snapshot
