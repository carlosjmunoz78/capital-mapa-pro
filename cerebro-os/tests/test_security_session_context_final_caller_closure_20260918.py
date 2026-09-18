from pathlib import Path

DOC = Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_FINAL_CALLER_CLOSURE_20260918.md")


def test_session_context_closure_records_all_discovered_callers():
    text = DOC.read_text()
    for name in (
        "fenix-b2b-actions",
        "fenix-ana-knowledge",
        "fenix-ana-canonical",
        "fenix-memory-api",
        "fenix-evidence-api",
        "fenix-ana-api",
        "fenix-document-intelligence-test",
        "fenix-document-intelligence",
        "fenix-document-extract",
        "fenix-communications-gateway",
        "fenix-document-reread",
        "fenix-document-auto-ingest",
        "fenix-document-existing-backfill",
    ):
        assert name in text


def test_only_guarded_backfill_and_http_e2e_keep_acl_retirement_blocked():
    text = DOC.read_text()
    assert "fenix-document-existing-backfill" in text
    assert "MUST NOT be revoked yet" in text
    assert "Authenticated HTTP E2E remains required" in text
    assert "POR_AUDITAR" in text
    assert "does not declare SECURITY green" in text
