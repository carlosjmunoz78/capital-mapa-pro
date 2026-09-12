from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "observability_cost_gate.py"
spec = importlib.util.spec_from_file_location("observability_cost_gate_runtime", MODULE)
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
        logs_ref="logs:ref",
        metrics_ref="metrics:ref",
        incident_ref="incidents:ref",
        cost_ref="cost:ref",
        monthly_cost_eur=0.0,
        money_limit_eur=0.0,
    )
    data.update(overrides)
    return mod.ObservabilityCostEvidence(**data)


def test_zero_cost_green_when_evidence_complete():
    result = mod.assess_observability_cost(evidence())
    assert result["green"] is True
    assert result["prod_candidate_allowed"] is True
    assert result["additional_paid_ai_required"] is False


def test_missing_cost_measurement_fails_closed():
    result = mod.assess_observability_cost(evidence(cost_ref="", monthly_cost_eur=None))
    assert result["green"] is False
    assert "cost_measured" in result["missing"]


def test_money_limit_is_canonical_human_exception():
    result = mod.assess_observability_cost(evidence(monthly_cost_eur=3.0, money_limit_eur=1.0))
    assert result["green"] is False
    assert result["limit_exceeded"] is True
    assert result["human_reason"] == "MONEY_LIMIT"
