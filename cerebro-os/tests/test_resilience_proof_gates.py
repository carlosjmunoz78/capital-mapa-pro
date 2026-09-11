from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "resilience" / "control_engines.py"

spec = importlib.util.spec_from_file_location("resilience_proof_gates", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_repair_cannot_green_without_pre_and_post_evidence():
    action = mod.RepairAction("fix", True, True, True, "rollback")
    assert action.allowed is False
    assert action.result == "BLOCKED"
    proven = mod.RepairAction("fix", True, True, True, "rollback", "pre:e", "post:e")
    assert proven.allowed is True
    assert proven.result == "GREEN"


def test_changed_regression_needs_approval_evidence():
    old = mod.RegressionBaseline("a", "b")
    new = mod.RegressionBaseline("a2", "b2")
    assert mod.regression_status(old, new, change_approved=True) == "RED"
    assert mod.regression_status(old, new, change_approved=True, approval_evidence_ref="approval:e") == "GREEN"


def test_continuity_booleans_and_runbook_alone_are_not_green():
    readiness = mod.ContinuityReadiness(True, True, True, True, "runbook")
    assert readiness.green is False


def test_continuity_requires_evidence_for_all_positive_dimensions():
    readiness = mod.ContinuityReadiness(
        True, True, True, True, "runbook", ("backup:e", "restore:e", "rebuild:e", "alternate:e")
    )
    assert readiness.green is True
