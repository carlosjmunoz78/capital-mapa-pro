from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "governance" / "promotion_gate.py"

spec = importlib.util.spec_from_file_location("promotion_evidence_gate", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_lab_can_be_green_with_boolean_gates_and_lab_test_evidence_elsewhere():
    result = mod.decide_promotion(engine_id="FACT-001", environment="LAB", gates=mod.all_green_gates())
    assert result["decision"] == "LAB_GREEN"
    assert result["missing_evidence"] == ()


def test_preprod_cannot_be_green_from_booleans_only():
    result = mod.decide_promotion(engine_id="FACT-001", environment="PREPROD", gates=mod.all_green_gates())
    assert result["decision"] == "BLOCKED"
    assert result["reason"] == "EVIDENCE_INCOMPLETE"
    assert set(result["missing_evidence"]) == set(mod.REQUIRED_GATES)


def test_prod_candidate_requires_evidence_for_every_gate():
    evidence = mod.evidence_for_all_gates("run-123")
    evidence.pop("rollback")
    result = mod.decide_promotion(
        engine_id="FACT-001", environment="PROD", gates=mod.all_green_gates(), evidence_refs=evidence
    )
    assert result["decision"] == "BLOCKED"
    assert result["missing_evidence"] == ("rollback",)


def test_prod_candidate_with_all_gate_evidence_is_allowed_to_candidate_only():
    result = mod.decide_promotion(
        engine_id="FACT-001",
        environment="PROD",
        gates=mod.all_green_gates(),
        evidence_refs=mod.evidence_for_all_gates("run-123"),
    )
    assert result["decision"] == "PROD_CANDIDATE"
    assert result["reason"] == "ALL_GATES_GREEN"
