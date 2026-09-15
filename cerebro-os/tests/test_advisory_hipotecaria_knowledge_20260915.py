import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "advisory" / "knowledge_validation_hipotecaria_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_hipotecaria_uses_bound_canonical_source():
    data = json.loads(VAL.read_text())
    assert data["domain"] == "HIPOTECARIA"
    assert data["source_sha256"] == "8a9aa63738e2b5d8bc6109e0760c2472ed757f3ccb6fbe3494ace2a38c4fd3ab"
    assert data["live_verification_required_per_case"] is True
    assert data["decision_support_only"] is True


def test_hipotecaria_official_checks_pass():
    data = json.loads(VAL.read_text())
    assert data["summary"]["checks"] >= 6
    assert data["summary"]["failed"] == 0
    assert data["summary"]["passed"] == data["summary"]["checks"]
    assert all(x["status"] == "PASS" for x in data["checks"])
    assert all(x["official_source"].startswith("https://") for x in data["checks"])


def test_hipotecaria_green_does_not_promote_capability_or_prod():
    data = json.loads(VAL.read_text())
    assert data["summary"]["knowledge_green"] is True
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False


def test_global_knowledge_ledger_is_eight_of_twelve():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["domains"] == 12
    assert data["summary"]["knowledge_green"] == 8
    assert data["summary"]["validation_pending"] == 4
    green = {x["domain"] for x in data["domains"] if x["status"] == "KNOWLEDGE_GREEN"}
    assert "HIPOTECARIA" in green
    assert len(green) == 8
