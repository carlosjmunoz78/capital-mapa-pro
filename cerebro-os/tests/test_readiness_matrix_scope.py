from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "registry" / "readiness_matrix.py"

spec = importlib.util.spec_from_file_location("readiness_matrix_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def rec(state: str, env: str, company: str = "fenix") -> dict:
    return {
        "engine_id": "APP-001",
        "company_id": company,
        "environment": env,
        "version": "1",
        "state": state,
        "evidence_refs": (f"evidence:{state}:{env}",) if state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"} else (),
    }


def test_unscoped_matrix_never_masks_prod_blocker_with_lab_green():
    matrix = mod.build_readiness_matrix(
        canonical_ids=("APP-001",),
        live_records=(rec("LAB_GREEN", "LAB"), rec("BLOCKED", "PROD")),
    )
    assert matrix[0]["state"] == "BLOCKED"
    assert matrix[0]["record_count"] == 2


def test_environment_scope_distinguishes_lab_from_prod():
    records = (rec("LAB_GREEN", "LAB"), rec("BLOCKED", "PROD"))
    lab = mod.build_readiness_matrix(canonical_ids=("APP-001",), live_records=records, environment="LAB")
    prod = mod.build_readiness_matrix(canonical_ids=("APP-001",), live_records=records, environment="PROD")
    assert lab[0]["state"] == "LAB_GREEN"
    assert prod[0]["state"] == "BLOCKED"


def test_company_scope_prevents_cross_company_status_leakage():
    records = (rec("CONFIRMED_OPERATIONAL", "PROD", "fenix"), rec("BLOCKED", "PROD", "other"))
    fenix = mod.build_readiness_matrix(
        canonical_ids=("APP-001",), live_records=records, company_id="fenix", environment="PROD"
    )
    assert fenix[0]["state"] == "CONFIRMED_OPERATIONAL"
    assert fenix[0]["record_count"] == 1


def test_missing_scope_is_unknown_not_inherited_from_another_company():
    matrix = mod.build_readiness_matrix(
        canonical_ids=("APP-001",), live_records=(rec("LAB_GREEN", "LAB", "other"),), company_id="fenix", environment="LAB"
    )
    assert matrix[0]["state"] == "UNKNOWN_REQUIRES_AUDIT"
    assert matrix[0]["record_count"] == 0


def test_invalid_environment_filter_rejected():
    try:
        mod.build_readiness_matrix(canonical_ids=("APP-001",), live_records=(), environment="STAGING")
    except ValueError as exc:
        assert "environment" in str(exc)
    else:
        raise AssertionError("expected invalid environment filter to fail")
