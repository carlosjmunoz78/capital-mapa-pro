from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "registry" / "live_status.py"

spec = importlib.util.spec_from_file_location("live_status_real_environment", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_blank_evidence_strings_do_not_satisfy_green():
    try:
        mod.make_status(
            engine_id="FACT-001", company_id="fenix", environment="LAB", version="1", state="LAB_GREEN", evidence_refs=("", "   ")
        )
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("blank evidence must fail")


def test_prod_operational_requires_promotion_gate_reference():
    try:
        mod.make_status(
            engine_id="FACT-001", company_id="fenix", environment="PROD", version="1", state="CONFIRMED_OPERATIONAL", evidence_refs=("ci:e",)
        )
    except ValueError as exc:
        assert "promotion_gate_ref" in str(exc)
    else:
        raise AssertionError("PROD operational claim without promotion evidence must fail")


def test_prod_operational_with_promotion_gate_reference_is_valid():
    record = mod.make_status(
        engine_id="FACT-001", company_id="fenix", environment="PROD", version="1", state="CONFIRMED_OPERATIONAL",
        evidence_refs=("ci:e", "rollback:e"), promotion_gate_ref="promotion:e",
    )
    assert record["state"] == "CONFIRMED_OPERATIONAL"
    assert record["promotion_gate_ref"] == "promotion:e"
