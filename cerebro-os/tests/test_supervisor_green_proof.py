from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "supervisor" / "system_loop.py"

spec = importlib.util.spec_from_file_location("supervisor_green_proof", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_claimed_lab_green_without_tests_reenters_test_phase():
    result = mod.loop_transition(state="LAB_GREEN", tests_green=False, evidence_present=True)
    assert result == {"phase": "TEST", "result": "IN_PROGRESS"}


def test_claimed_green_without_evidence_reenters_evidence_phase():
    result = mod.loop_transition(state="CONFIRMED_OPERATIONAL", tests_green=True, evidence_present=False)
    assert result == {"phase": "EVIDENCE", "result": "IN_PROGRESS"}


def test_claimed_green_with_tests_and_evidence_is_terminal():
    result = mod.loop_transition(state="LAB_GREEN", tests_green=True, evidence_present=True)
    assert result == {"phase": "DONE", "result": "GREEN"}


def test_system_cannot_be_green_with_blocked_count():
    try:
        mod.system_loop_status(canonical_count=177, green_count=177, blocked_count=1)
    except ValueError as exc:
        assert "non-green" in str(exc)
    else:
        raise AssertionError("inconsistent green/blocked counts must fail")


def test_system_human_required_has_precedence_over_red():
    result = mod.system_loop_status(canonical_count=177, green_count=175, blocked_count=1, human_count=1)
    assert result["state"] == "HUMAN_REQUIRED"
    assert result["pending"] == 2
