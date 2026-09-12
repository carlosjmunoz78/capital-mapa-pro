from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "core_generic_legacy_contract.py"
FIXTURE = ROOT / "runtime" / "fixtures" / "core_generic_legacy_live_contract_2026-09-12.json"

spec = importlib.util.spec_from_file_location("core_generic_legacy_contract", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_live_fixture_is_green_fail_closed():
    result = mod.validate_generic_core_legacy_contract(mod.load_fixture(FIXTURE))
    assert result["status"] == "GREEN_CODE_CI"
    assert result["scenario_count"] == 4
    assert result["old_preserved"] is True
    assert result["auto_activate_allowed"] is False
    assert result["delete_allowed"] is False
    assert result["external_action_allowed"] is False


def test_missing_scenario_is_red():
    data = mod.load_fixture(FIXTURE)
    data["scenarios"] = [item for item in data["scenarios"] if item["scenario_id"] != 9527140]
    result = mod.validate_generic_core_legacy_contract(data)
    assert result["status"] == "RED"
    assert any("missing_scenarios" in failure for failure in result["failures"])


def test_dispatcher_cannot_relax_t48_or_call_platform():
    data = mod.load_fixture(FIXTURE)
    item = next(item for item in data["scenarios"] if item["scenario_id"] == 9537817)
    item["expected"]["requires_t48_hash"] = False
    item["expected"]["platform_state"] = "CALLED"
    result = mod.validate_generic_core_legacy_contract(data)
    assert result["status"] == "RED"
    assert "9537817:requires_t48_hash_not_required" in result["failures"]
    assert "9537817:platform_must_not_be_called" in result["failures"]


def test_any_activation_or_external_action_claim_is_red():
    data = mod.load_fixture(FIXTURE)
    data["scenarios"][0]["status"] = "active"
    data["scenarios"][1]["expected"]["external_action_allowed"] = True
    result = mod.validate_generic_core_legacy_contract(data)
    assert result["status"] == "RED"
