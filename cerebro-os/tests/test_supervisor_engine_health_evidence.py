from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "supervisor" / "supervisor.py"

spec = importlib.util.spec_from_file_location("supervisor_engine_health_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def health(**overrides):
    values = dict(
        engine_id="FACT-001",
        tests_green=True,
        evaluation_green=True,
        tribunal_green=True,
        rollback_ready=True,
        observability_ready=True,
        company_id="fenix-capital",
        environment="PROD",
        evidence_refs=("tests:e", "evaluation:e", "tribunal:e", "rollback:e", "observability:e"),
    )
    values.update(overrides)
    return mod.EngineHealth(**values)


def test_boolean_only_engine_health_is_not_green():
    assert health(evidence_refs=()).state == mod.RED


def test_complete_scoped_engine_health_can_be_green():
    assert health().state == mod.GREEN


def test_invalid_environment_fails_closed():
    assert health(environment="STAGING").state == mod.RED


def test_human_required_precedes_green_checks():
    assert health(human_required=True).state == mod.HUMAN_REQUIRED


def test_partial_evidence_is_not_green():
    assert health(evidence_refs=("tests:e", "evaluation:e")).state == mod.RED
