from pathlib import Path

DOC=Path("cerebro-os/evidence/finops/FINOPS_GMAIL_BILLING_EVIDENCE_20260919.md")

def test_finops_gmail_evidence_remains_fail_closed():
    text=DOC.read_text()
    assert "exact Google Cloud monthly amount remains POR_AUDITAR" in text
    assert "does NOT independently prove" in text
    assert "FINOPS:monthly_cost_measured" in text
    assert "No amount is inferred" in text
