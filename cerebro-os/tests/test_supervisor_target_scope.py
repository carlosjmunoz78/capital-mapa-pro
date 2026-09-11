from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "supervisor" / "loop_controller.py"

spec = importlib.util.spec_from_file_location("supervisor_target_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

LAB_ROW = {"engine_id": "FACT-001", "state": "LAB_GREEN", "environment": "LAB", "company_id": "GLOBAL", "evidence_refs": ("lab:e",)}


def test_lab_green_is_terminal_for_lab_target():
    assert mod.select_next_engine((LAB_ROW,), target_environment="LAB", company_id="fenix") is None
    assert mod.next_action(LAB_ROW, target_environment="LAB", company_id="fenix")["action"] == "SKIP_GREEN"


def test_lab_green_is_not_terminal_for_prod_target():
    selected = mod.select_next_engine((LAB_ROW,), target_environment="PROD", company_id="fenix")
    assert selected["engine_id"] == "FACT-001"
    assert mod.next_action(LAB_ROW, target_environment="PROD", company_id="fenix")["action"] == "PROMOTION_GAP_ANALYSIS"


def test_green_without_evidence_is_not_terminal():
    row = dict(LAB_ROW, evidence_refs=())
    assert mod.select_next_engine((row,), target_environment="LAB", company_id="fenix") is not None


def test_cross_company_confirmed_operational_is_not_skipped():
    row = {"engine_id": "APP-001", "state": "CONFIRMED_OPERATIONAL", "environment": "PROD", "company_id": "other", "evidence_refs": ("e",)}
    assert mod.next_action(row, target_environment="PROD", company_id="fenix")["action"] == "SCOPE_AUDIT"
