from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "recovery_readiness.py"
spec = importlib.util.spec_from_file_location("recovery_readiness_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_source_recovery_is_not_provider_restore():
    evidence = mod.RecoveryEvidence(
        company_id="fenix",
        environment="PREPROD",
        version="1.0.0",
        source_backup_ref="git:sha",
        rebuild_ref="ci:build",
        rollback_rehearsal_ref="actions:run",
        provider_restore_ref="",
    )
    result = mod.assess_recovery_readiness(evidence)
    assert result["source_recovery_green"] is True
    assert result["provider_restore_green"] is False
    assert result["recovery_green"] is False
    assert result["prod_candidate_allowed"] is False
    assert result["destructive_restore_allowed"] is False


def test_complete_evidence_can_be_green_without_enabling_destructive_restore():
    evidence = mod.RecoveryEvidence(
        company_id="fenix",
        environment="PREPROD",
        version="1.0.0",
        source_backup_ref="git:sha",
        rebuild_ref="ci:build",
        rollback_rehearsal_ref="actions:run",
        provider_restore_ref="provider:restore-drill",
    )
    result = mod.assess_recovery_readiness(evidence)
    assert result["recovery_green"] is True
    assert result["prod_candidate_allowed"] is True
    assert result["destructive_restore_allowed"] is False


def test_prod_missing_recovery_evidence_is_high_risk_fail_closed():
    evidence = mod.RecoveryEvidence(company_id="fenix", environment="PROD", version="1.0.0")
    result = mod.assess_recovery_readiness(evidence)
    assert result["recovery_green"] is False
    assert result["human_reason"] == "HIGH_RISK"
    assert set(result["missing"]) == {"source_backup", "rebuild", "rollback_rehearsal", "provider_restore"}
