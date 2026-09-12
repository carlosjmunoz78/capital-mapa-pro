from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "promotion_gate.py"
spec = importlib.util.spec_from_file_location("promotion_gate_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def evidence(**overrides):
    data = dict(
        company_id="fenix",
        engine_id="ENG-001",
        environment="PREPROD",
        version="1.0.0",
        contracts=True,
        permissions=True,
        tests=True,
        evaluation=True,
        tribunal=True,
        observability=True,
        rollback=True,
        backup=True,
        rebuild=True,
        cost_measured=True,
        policy=True,
        environment_evidence=True,
        human_reason=None,
    )
    data.update(overrides)
    return mod.PromotionEvidence(**data)


def test_all_technical_gates_yield_prod_candidate_not_prod_green():
    result = mod.assess_promotion(evidence())
    assert result["technical_green"] is True
    assert result["prod_candidate"] is True
    assert result["prod_green"] is False
    assert result["gradual_promotion_required"] is True
    assert result["automatic_external_action_allowed"] is False


def test_missing_recovery_or_observability_blocks_candidate():
    result = mod.assess_promotion(evidence(rollback=False, observability=False))
    assert result["prod_candidate"] is False
    assert set(result["missing"]) == {"rollback", "observability"}


def test_canonical_human_exception_blocks_candidate():
    result = mod.assess_promotion(evidence(human_reason="MONEY_LIMIT"))
    assert result["technical_green"] is True
    assert result["human_blocked"] is True
    assert result["prod_candidate"] is False


def test_noncanonical_human_reason_is_rejected():
    try:
        mod.assess_promotion(evidence(human_reason="OTHER_REASON"))
    except ValueError as exc:
        assert "non-canonical" in str(exc)
    else:
        raise AssertionError("expected ValueError")
