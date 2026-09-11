from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "onboarding" / "executor.py"

spec = importlib.util.spec_from_file_location("onboarding_executor_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_phase_cannot_green_without_evidence():
    executor = mod.OnboardingExecutor("fenix", environment="PROD")
    try:
        executor.mark_green(mod.CANONICAL_PHASES[0])
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("phase green without evidence must fail")


def test_cross_environment_phase_update_is_denied():
    executor = mod.OnboardingExecutor("fenix", environment="PROD")
    try:
        executor.mark_green(mod.CANONICAL_PHASES[0], evidence_refs=("e",), environment="LAB")
    except ValueError as exc:
        assert "environment" in str(exc)
    else:
        raise AssertionError("cross-environment phase update must fail")


def test_all_phases_with_evidence_complete_green():
    executor = mod.OnboardingExecutor("fenix", environment="LAB")
    for phase in mod.CANONICAL_PHASES:
        executor.mark_green(phase, evidence_refs=(f"e:{phase}",))
    assert executor.state == "GREEN"
    assert executor.next_phase() is None


def test_red_phase_remains_retryable_without_losing_order():
    executor = mod.OnboardingExecutor("fenix")
    first = mod.CANONICAL_PHASES[0]
    executor.mark_red(first, "test failure")
    assert executor.state == "RED"
    executor.retry(first)
    assert executor.state == "IN_PROGRESS"
    assert executor.next_phase() == first
