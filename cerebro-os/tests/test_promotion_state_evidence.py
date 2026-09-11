from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "governance" / "promotion.py"

spec = importlib.util.spec_from_file_location("promotion_state_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def refs() -> dict[str, str]:
    return {key: f"evidence:{key}" for key in mod.PROD_EVIDENCE_KEYS}


def advance_to_preprod() -> object:
    state = mod.PromotionState()
    state.transition("LAB_GREEN", gates_green=True, rollback_verified=True, backup_verified=True)
    state.transition("PREPROD_GREEN", gates_green=True, rollback_verified=True, backup_verified=True)
    return state


def test_boolean_only_path_cannot_reach_prod_candidate():
    state = advance_to_preprod()
    try:
        state.transition("PROD_CANDIDATE", gates_green=True, rollback_verified=True, backup_verified=True)
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("boolean-only production promotion must fail")


def test_prod_candidate_requires_complete_evidence():
    state = advance_to_preprod()
    evidence = refs()
    evidence.pop("backup")
    try:
        state.transition(
            "PROD_CANDIDATE",
            gates_green=True,
            rollback_verified=True,
            backup_verified=True,
            evidence_refs=evidence,
        )
    except ValueError as exc:
        assert "backup" in str(exc)
    else:
        raise AssertionError("missing production evidence must fail")


def test_complete_evidence_allows_candidate_then_prod():
    state = advance_to_preprod()
    evidence = refs()
    assert state.transition(
        "PROD_CANDIDATE",
        gates_green=True,
        rollback_verified=True,
        backup_verified=True,
        evidence_refs=evidence,
    ) == "PROD_CANDIDATE"
    assert state.transition(
        "PROD",
        gates_green=True,
        rollback_verified=True,
        backup_verified=True,
        evidence_refs=evidence,
    ) == "PROD"
