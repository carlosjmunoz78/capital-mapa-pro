from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "quality" / "tribunal.py"

spec = importlib.util.spec_from_file_location("tribunal_evidence_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def green_gates():
    return {gate: True for gate in mod.REQUIRED_GATES}


def green_evidence():
    return {gate: f"e:{gate}" for gate in mod.REQUIRED_GATES}


def test_boolean_only_tribunal_is_not_approved():
    decision = mod.TribunalDecision("FACT-001", green_gates())
    assert decision.approved is False
    assert set(decision.missing_evidence()) == set(mod.REQUIRED_GATES)


def test_complete_scoped_tribunal_can_approve():
    decision = mod.TribunalDecision(
        "FACT-001", green_gates(), company_id="fenix", environment="PROD", evidence_refs=green_evidence()
    )
    assert decision.approved is True


def test_missing_tenant_isolation_fails_closed():
    gates = green_gates()
    gates["tenant_isolation"] = False
    decision = mod.TribunalDecision("FACT-001", gates, company_id="fenix", environment="PROD", evidence_refs=green_evidence())
    assert decision.approved is False
    assert decision.missing() == ("tenant_isolation",)


def test_invalid_environment_is_not_approved():
    decision = mod.TribunalDecision("FACT-001", green_gates(), company_id="fenix", environment="STAGING", evidence_refs=green_evidence())
    assert decision.approved is False
