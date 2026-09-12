from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "factory_inactive_adapter_contract.py"
FIXTURE = ROOT / "runtime" / "fixtures" / "factory_inactive_adapters_live_contract_2026-09-12.json"

spec = importlib.util.spec_from_file_location("factory_inactive_adapter_contract", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_live_factory_adapters_are_green_and_zero_cost():
    result = mod.validate_factory_adapters(mod.load_fixture(FIXTURE))
    assert result["status"] == "GREEN_CODE_CI"
    assert result["adapter_count"] == 5
    assert result["preserve_legacy"] is True
    assert result["external_action_allowed"] is False
    assert result["additional_cost_required"] is False


def test_activation_or_external_action_claim_turns_red():
    data = mod.load_fixture(FIXTURE)
    data["adapters"][0]["status"] = "active"
    data["adapters"][1]["external_action_allowed"] = True
    assert mod.validate_factory_adapters(data)["status"] == "RED"


def test_paid_provider_requirement_is_forbidden_by_default():
    data = mod.load_fixture(FIXTURE)
    data["policy"]["paid_provider_required"] = True
    data["policy"]["paid_ai_required"] = True
    result = mod.validate_factory_adapters(data)
    assert result["status"] == "RED"
    assert "policy:paid_provider_required" in result["failures"]
    assert "policy:paid_ai_required" in result["failures"]


def test_missing_adapter_is_red():
    data = mod.load_fixture(FIXTURE)
    data["adapters"] = data["adapters"][:-1]
    result = mod.validate_factory_adapters(data)
    assert result["status"] == "RED"
    assert any(f.startswith("missing:") for f in result["failures"])
