from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "runtime" / "dependency_contract_gate.py"
spec = importlib.util.spec_from_file_location("dependency_contract_gate_runtime", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def full_evidence(**overrides):
    data = dict(
        company_id="fenix",
        engine_id="ENG-001",
        environment="PREPROD",
        version="1.0.0",
        inventory_ref="inventory:ref",
        dependency_map_ref="deps:ref",
        current_contract_ref="contract:ref",
        behavior_tests_ref="tests:ref",
        parallel_impl_ref="parallel:ref",
        rollback_ref="rollback:ref",
        covered_systems=mod.REQUIRED_SYSTEMS,
    )
    data.update(overrides)
    return mod.DependencyContractEvidence(**data)


def test_complete_preservation_contract_can_be_green():
    result = mod.assess_dependency_contract(full_evidence())
    assert result["green"] is True
    assert result["prod_candidate_allowed"] is True
    assert result["old_systems_may_be_deleted"] is False


def test_missing_app_crm_dependency_coverage_fails_closed():
    covered = tuple(system for system in mod.REQUIRED_SYSTEMS if system not in {"app", "crm"})
    result = mod.assess_dependency_contract(full_evidence(covered_systems=covered))
    assert result["green"] is False
    assert set(result["missing_systems"]) == {"app", "crm"}


def test_missing_old_behavior_tests_blocks_migration():
    result = mod.assess_dependency_contract(full_evidence(behavior_tests_ref=""))
    assert result["green"] is False
    assert "behavior_tests" in result["missing_evidence"]
    assert result["migration_rule"] == "CONSERVAR_ENTENDER_ENVOLVER_PROBAR_MEJORAR_MIGRAR"
