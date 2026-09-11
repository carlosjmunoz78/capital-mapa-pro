from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "processes" / "platform_loop_controller.py"

spec = importlib.util.spec_from_file_location("platform_loop_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

LOOPS = {"L": ("FACT-001", "GOV-001")}


def test_prod_controller_rejects_lab_result():
    ctl = mod.PlatformLoopController("fenix", LOOPS, set(), environment="PROD")
    result = mod.EngineResult("fenix", "L", "FACT-001", "LAB", "GREEN", evidence_ref="e")
    try:
        ctl.update(result)
    except ValueError as exc:
        assert "environment" in str(exc)
    else:
        raise AssertionError("cross-environment result must fail")


def test_green_sequence_requires_evidence_and_order():
    ctl = mod.PlatformLoopController("fenix", LOOPS, set(), environment="LAB")
    ctl.update(mod.EngineResult("fenix", "L", "FACT-001", "LAB", "GREEN", evidence_ref="e:fact"))
    ctl.update(mod.EngineResult("fenix", "L", "GOV-001", "LAB", "GREEN", evidence_ref="e:gov"))
    assert ctl.loop_status("L") == "GREEN"
    assert ctl.system_status() == "GREEN"


def test_cross_company_result_is_rejected():
    ctl = mod.PlatformLoopController("fenix", LOOPS, set(), environment="LAB")
    result = mod.EngineResult("other", "L", "FACT-001", "LAB", "GREEN", evidence_ref="e")
    try:
        ctl.update(result)
    except ValueError as exc:
        assert "company" in str(exc)
    else:
        raise AssertionError("cross-company result must fail")


def test_lab_only_engine_cannot_exist_in_prod_controller():
    try:
        mod.PlatformLoopController("fenix", {"L": ("LAB-TRD",)}, {"LAB-TRD"}, environment="PROD")
    except ValueError as exc:
        assert "LAB-only" in str(exc)
    else:
        raise AssertionError("LAB-only engine in PROD controller must fail")
