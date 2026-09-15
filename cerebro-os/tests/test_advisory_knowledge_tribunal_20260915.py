import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIBUNAL = ROOT / "advisory" / "advisory_knowledge_tribunal_20260915.json"
STATUS = ROOT / "advisory" / "knowledge_status_20260915.json"


def test_tribunal_has_exactly_twelve_bound_domains():
    data = json.loads(TRIBUNAL.read_text())
    assert len(data["domains"]) == 12
    assert len({x["domain"] for x in data["domains"]}) == 12
    assert all(len(x["source_sha256"]) == 64 for x in data["domains"])
    assert all(x["evidence"] for x in data["domains"])


def test_global_ledger_is_12_of_12():
    data = json.loads(STATUS.read_text())
    assert data["summary"]["domains"] == 12
    assert data["summary"]["knowledge_green"] == 12
    assert data["summary"]["validation_pending"] == 0
    assert all(x["status"] == "KNOWLEDGE_GREEN" for x in data["domains"])


def test_tribunal_passes_knowledge_only():
    data = json.loads(TRIBUNAL.read_text())
    assert data["result"]["knowledge_tribunal"] == "PASS"
    assert data["result"]["knowledge_green_12_of_12"] is True
    checks = data["checks"]
    assert checks["all_12_knowledge_green"] is True
    assert checks["all_12_sources_bound_with_sha256"] is True
    assert checks["domain_evidence_registered"] is True
    assert checks["live_verification_required_for_dynamic_or_high_risk_facts"] is True
    assert checks["regulated_actions_not_promoted"] is True


def test_tribunal_does_not_promote_capability_autonomy_or_prod():
    data = json.loads(TRIBUNAL.read_text())
    checks = data["checks"]
    assert checks["capability_green"] is False
    assert checks["autonomy_green"] is False
    assert checks["prod_enabled"] is False
    assert checks["app_crm_prod_touched"] is False
