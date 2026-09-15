import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "advisory" / "knowledge_validation_patrimonial_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_patrimonial_uses_bound_canonical_source():
    data = json.loads(VAL.read_text())
    assert data["domain"] == "PATRIMONIAL"
    assert data["source_sha256"] == "8dd142ebfb4858cb45955fab2537eda5e6bc31d64cbff9f333194b23cc80e134"
    assert data["live_verification_required_per_case"] is True
    assert data["decision_support_only"] is True


def test_patrimonial_official_checks_pass():
    data = json.loads(VAL.read_text())
    assert data["summary"]["checks"] >= 6
    assert data["summary"]["failed"] == 0
    assert data["summary"]["passed"] == data["summary"]["checks"]
    assert all(x["status"] == "PASS" for x in data["checks"])
    assert all(x["official_source"].startswith("https://") for x in data["checks"])


def test_patrimonial_green_does_not_promote_capability_or_prod():
    data = json.loads(VAL.read_text())
    assert data["summary"]["knowledge_green"] is True
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False


def test_global_knowledge_ledger_is_twelve_of_twelve():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["domains"] == 12
    assert data["summary"]["knowledge_green"] == 12
    assert data["summary"]["validation_pending"] == 0
    green = {x["domain"] for x in data["domains"] if x["status"] == "KNOWLEDGE_GREEN"}
    assert "PATRIMONIAL" in green
    assert len(green) == 12
