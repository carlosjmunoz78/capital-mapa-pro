import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "advisory" / "knowledge_validation_financiera_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_financiera_uses_bound_canonical_source():
    data = json.loads(VAL.read_text())
    assert data["domain"] == "FINANCIERA"
    assert data["source_sha256"] == "d5493adfbbdfc62b10183dabde07192625b17046901eb40cbf8b7c5bdeeab1d7"
    assert data["decision_support_only"] is True
    assert data["live_verification_required_per_case"] is True


def test_financiera_official_checks_pass():
    data = json.loads(VAL.read_text())
    assert data["summary"]["checks"] >= 6
    assert data["summary"]["failed"] == 0
    assert data["summary"]["passed"] == data["summary"]["checks"]
    assert all(x["status"] == "PASS" for x in data["checks"])
    assert all(x["official_source"].startswith("https://") for x in data["checks"])


def test_financiera_dynamic_bank_criteria_remain_live_checked():
    data = json.loads(VAL.read_text())
    gates = " ".join(data["domain_specific_gates"]).lower()
    assert "bank-specific criteria" in gates
    assert "verbal experience" in gates
    assert "cirbe" in gates


def test_financiera_green_does_not_promote_capability_or_prod():
    data = json.loads(VAL.read_text())
    assert data["summary"]["knowledge_green"] is True
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False


def test_global_knowledge_ledger_is_six_of_twelve():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["domains"] == 12
    assert data["summary"]["knowledge_green"] == 6
    assert data["summary"]["validation_pending"] == 6
