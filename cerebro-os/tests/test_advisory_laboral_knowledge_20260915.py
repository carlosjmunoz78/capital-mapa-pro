import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "advisory" / "knowledge_validation_laboral_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_laboral_uses_bound_canonical_source():
    data = json.loads(VAL.read_text())
    assert data["domain"] == "LABORAL"
    assert data["source_sha256"] == "a3d27920a7d7f914cca6b82d05a37fa787a6cd7c9699cdbe5bc129a51b6810bc"
    assert data["live_verification_required_per_case"] is True
    assert data["decision_support_only"] is True


def test_laboral_official_checks_pass():
    data = json.loads(VAL.read_text())
    assert data["summary"]["checks"] >= 8
    assert data["summary"]["failed"] == 0
    assert data["summary"]["passed"] == data["summary"]["checks"]
    assert all(x["status"] == "PASS" for x in data["checks"])
    assert all(x["official_source"].startswith("https://") for x in data["checks"])


def test_laboral_green_does_not_promote_capability_or_prod():
    data = json.loads(VAL.read_text())
    assert data["summary"]["knowledge_green"] is True
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False


def test_global_knowledge_ledger_is_four_of_twelve():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["domains"] == 12
    assert data["summary"]["knowledge_green"] == 4
    assert data["summary"]["validation_pending"] == 8
    green = {x["domain"] for x in data["domains"] if x["status"] == "KNOWLEDGE_GREEN"}
    assert green == {"FISCAL", "CONTABLE", "LABORAL", "JURIDICA_GENERAL"}
