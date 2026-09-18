from pathlib import Path

DOC=Path("cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_ZERO_EDGE_CALLERS_20260919.md")

def test_zero_edge_caller_evidence_stays_fail_closed():
    text=DOC.read_text()
    assert "version: `8`" in text
    assert "cfe78207a52d5edaab2a02c1938394d55cd8e28aeef0c1acea2edcfc907de810" in text
    assert "known ACTIVE Edge Function direct-caller count" in text
    assert "`0`" in text
    assert "AUTORIZO RETIRO SELECTIVO RPC PROD" in text
    assert "NOT been revoked yet" in text
    assert "does NOT declare global SECURITY green" in text
