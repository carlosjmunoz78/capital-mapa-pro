import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_professional_advisory_is_orchestrator_not_new_engine():
    data = json.loads((ROOT / "advisory" / "professional_advisory.manifest.json").read_text())
    assert data["component_type"] == "CAPABILITY_ORCHESTRATOR"
    assert data["engine_id"] is None
    assert data["create_new_engine_id"] is False
    assert data["promotion"]["prod_enabled"] is False


def test_fiscal_is_specialty_not_root_component():
    data = json.loads((ROOT / "advisory" / "professional_advisory.manifest.json").read_text())
    assert "FISCAL" in data["domains"]
    assert len(data["domains"]) == 12
    assert any("TAX-001 is the Fiscal capability" in note for note in data["notes"])


def test_no_false_green_from_architecture_only():
    data = json.loads((ROOT / "advisory" / "professional_advisory.manifest.json").read_text())
    assert data["promotion"] == {
        "knowledge_green": False,
        "capability_green": False,
        "autonomy_green": False,
        "prod_enabled": False,
    }
