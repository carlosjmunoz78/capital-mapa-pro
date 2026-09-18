from pathlib import Path

DOC = Path("cerebro-os/evidence/security/SUPABASE_PROD_FINAL_BACKFILL_CALLER_CANDIDATE_20260919.md")
SRC = Path("cerebro-os/evidence/security/deploy-candidates/fenix-document-existing-backfill-v8.ts")


def test_final_backfill_candidate_removes_direct_legacy_session_context_call():
    src = SRC.read_text()
    assert "fenix_prod_actor_context_by_auth_server" in src
    assert "user.auth.getUser" in src
    assert "rpc('fenix_prod_session_context')" not in src


def test_candidate_is_not_misrepresented_as_deployed_or_authorized():
    text = DOC.read_text()
    assert "NOT DEPLOYED" in text
    assert "NOT evidence of a live deployment" in text
    assert "No SQL ACL retirement is authorized" in text
    assert "explicit authorization" in text
