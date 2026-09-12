from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "external_evidence_queue.py"
spec = importlib.util.spec_from_file_location("external_evidence_queue_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def gap(gap_id: str, reason: str, engine_id: str = "ENG-001"):
    return mod.EvidenceGap(
        company_id="fenix",
        engine_id=engine_id,
        environment="PREPROD",
        version="1.0.0",
        gap_id=gap_id,
        reason=reason,
        evidence_needed="proof",
    )


def test_high_risk_precedes_external_proof():
    queue = mod.build_queue((gap("provider-restore", "EXTERNAL_PROOF"), gap("rollback", "HIGH_RISK")))
    assert queue[0]["gap_id"] == "rollback"
    assert queue[1]["gap_id"] == "provider-restore"


def test_queue_is_deterministic_for_same_priority():
    queue = mod.build_queue((gap("b", "EXTERNAL_PROOF", "ENG-B"), gap("a", "EXTERNAL_PROOF", "ENG-A")))
    assert [item["engine_id"] for item in queue] == ["ENG-A", "ENG-B"]


def test_unknown_reason_is_rejected():
    try:
        mod.build_queue((gap("x", "NOT_CANONICAL"),))
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("expected ValueError")
