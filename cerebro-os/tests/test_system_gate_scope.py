from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "registry" / "system_gate.py"

spec = importlib.util.spec_from_file_location("system_gate_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

CANONICAL = tuple(json.loads((ROOT / "registry" / "canonical_177.json").read_text(encoding="utf-8"))["engine_ids"])


def matrix(state: str, environment: str, company_id: str = "fenix") -> tuple[dict, ...]:
    return tuple({"engine_id": engine_id, "state": state, "environment": environment, "company_id": company_id} for engine_id in CANONICAL)


def test_lab_green_is_valid_only_for_lab_system_gate():
    result = mod.system_readiness(canonical_ids=CANONICAL, matrix=matrix("LAB_GREEN", "LAB"), environment="LAB", company_id="fenix")
    assert result["state"] == "GREEN"
    prod = mod.system_readiness(canonical_ids=CANONICAL, matrix=matrix("LAB_GREEN", "PROD"), environment="PROD", company_id="fenix")
    assert prod["state"] == "RED"
    assert len(prod["not_green"]) == 177


def test_prod_requires_confirmed_operational_for_every_engine():
    result = mod.system_readiness(canonical_ids=CANONICAL, matrix=matrix("CONFIRMED_OPERATIONAL", "PROD"), environment="PROD", company_id="fenix")
    assert result["state"] == "GREEN"
    assert result["green_count"] == 177


def test_cross_company_rows_cannot_satisfy_gate():
    result = mod.system_readiness(canonical_ids=CANONICAL, matrix=matrix("CONFIRMED_OPERATIONAL", "PROD", "other"), environment="PROD", company_id="fenix")
    assert result["state"] == "RED"
    assert len(result["missing_rows"]) == 177
    assert len(result["scope_errors"]) == 177


def test_wrong_environment_rows_cannot_satisfy_prod_gate():
    result = mod.system_readiness(canonical_ids=CANONICAL, matrix=matrix("CONFIRMED_OPERATIONAL", "LAB"), environment="PROD", company_id="fenix")
    assert result["state"] == "RED"
    assert len(result["missing_rows"]) == 177


def test_duplicate_rows_fail_closed():
    rows = list(matrix("CONFIRMED_OPERATIONAL", "PROD"))
    rows.append(dict(rows[0]))
    result = mod.system_readiness(canonical_ids=CANONICAL, matrix=tuple(rows), environment="PROD", company_id="fenix")
    assert result["state"] == "RED"
    assert rows[0]["engine_id"] in result["scope_errors"]
