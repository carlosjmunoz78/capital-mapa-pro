from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "registry" / "promotion_gap_queue.py"

spec = importlib.util.spec_from_file_location("promotion_gap_queue", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

CANONICAL = tuple(json.loads((ROOT / "registry" / "canonical_177.json").read_text(encoding="utf-8"))["engine_ids"])


def full_refs(prefix: str) -> dict[str, str]:
    return {gate: f"{prefix}:{gate}" for gate in mod.REQUIRED_GATES}


def test_no_real_evidence_means_all_177_engines_stay_in_prod_gap_queue():
    queue = mod.build_promotion_gap_queue(
        canonical_ids=CANONICAL,
        company_id="fenix-capital",
        target_environment="PROD",
        evidence_by_engine={},
    )
    assert len(queue) == 177
    assert all(row["missing_count"] == len(mod.REQUIRED_GATES) for row in queue)


def test_one_fully_evidenced_engine_is_ready_for_gate_but_not_auto_promoted():
    evidence = {CANONICAL[0]: full_refs("proof")}
    queue = mod.build_promotion_gap_queue(
        canonical_ids=CANONICAL,
        company_id="fenix-capital",
        target_environment="PROD",
        evidence_by_engine=evidence,
    )
    ready = mod.ready_for_gate(
        canonical_ids=CANONICAL,
        company_id="fenix-capital",
        target_environment="PROD",
        evidence_by_engine=evidence,
    )
    assert len(queue) == 176
    assert ready == (CANONICAL[0],)


def test_partial_evidence_reports_exact_missing_gates():
    refs = full_refs("proof")
    refs.pop("rollback")
    refs.pop("backup")
    queue = mod.build_promotion_gap_queue(
        canonical_ids=("FACT-001",),
        company_id="fenix-capital",
        target_environment="PREPROD",
        evidence_by_engine={"FACT-001": refs},
    )
    assert queue[0]["missing_gates"] == ("rollback", "backup")


def test_unknown_engine_evidence_is_rejected():
    try:
        mod.build_promotion_gap_queue(
            canonical_ids=("FACT-001",),
            company_id="fenix-capital",
            target_environment="PROD",
            evidence_by_engine={"NOT-CANONICAL": full_refs("x")},
        )
    except ValueError as exc:
        assert "non-canonical" in str(exc)
    else:
        raise AssertionError("non-canonical evidence must fail")
