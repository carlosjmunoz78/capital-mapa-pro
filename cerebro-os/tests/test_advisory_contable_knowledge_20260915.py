import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "advisory" / "knowledge_validation_contable_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_contable_uses_bound_source_hash():
    data = json.loads(VAL.read_text())
    assert data["domain"] == "CONTABLE"
    assert data["source_sha256"] == "547b7c0c29d7c13223340acd77548a6ff351a031fc0c1408e25b152d4183d0be"
    assert data["decision_support_only"] is True
    assert data["live_verification_required_per_case"] is True


def test_contable_official_checks_pass():
    data = json.loads(VAL.read_text())
    assert data["summary"]["checks"] >= 7
    assert data["summary"]["failed"] == 0
    assert data["summary"]["passed"] == data["summary"]["checks"]
    assert all(row["status"] == "PASS" for row in data["checks"])
    assert all(row["official_source"].startswith("https://") for row in data["checks"])


def test_contable_green_does_not_promote_capability_or_prod():
    data = json.loads(VAL.read_text())
    assert data["summary"]["knowledge_green"] is True
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False


def test_global_knowledge_ledger_is_three_of_twelve():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["knowledge_green"] == 3
    assert data["summary"]["validation_pending"] == 9
    green = {row["domain"] for row in data["domains"] if row["status"] == "KNOWLEDGE_GREEN"}
    assert green == {"FISCAL", "CONTABLE", "JURIDICA_GENERAL"}
