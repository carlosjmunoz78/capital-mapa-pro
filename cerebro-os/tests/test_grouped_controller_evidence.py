from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "processes" / "grouped_controller.py"

spec = importlib.util.spec_from_file_location("grouped_controller_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_green_without_evidence_is_rejected():
    ctl = mod.GroupedProcessController(company_id="fenix", environment="PROD")
    try:
        ctl.update_family("notifications", "GREEN")
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("GREEN without evidence must fail")


def test_cross_environment_update_is_rejected():
    ctl = mod.GroupedProcessController(company_id="fenix", environment="PROD")
    try:
        ctl.update_family("notifications", "GREEN", evidence_refs=("e",), environment="LAB")
    except ValueError as exc:
        assert "environment" in str(exc)
    else:
        raise AssertionError("cross-environment update must fail")


def test_macro_green_requires_every_family_green_with_evidence():
    ctl = mod.GroupedProcessController(company_id="fenix", environment="LAB")
    for family in mod.MACRO_LOOPS["LOOP-25-COMMS"]:
        ctl.update_family(family, "GREEN", evidence_refs=(f"e:{family}",))
    assert ctl.macro_status("LOOP-25-COMMS") == "GREEN"
    assert ctl.system_status() == "IN_PROGRESS"


def test_system_preserves_blocked_precedence():
    ctl = mod.GroupedProcessController(company_id="fenix", environment="LAB")
    ctl.update_family("notifications", "BLOCKED")
    assert ctl.system_status() == "BLOCKED"
