from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "registry" / "audit_queue.py"

spec = importlib.util.spec_from_file_location("audit_queue_target_environment", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

CANONICAL = tuple(json.loads((ROOT / "registry" / "canonical_177.json").read_text(encoding="utf-8"))["engine_ids"])


def lab_green_matrix() -> tuple[dict, ...]:
    return tuple({"engine_id": e, "state": "LAB_GREEN", "environment": "LAB", "company_id": "GLOBAL"} for e in CANONICAL)


def test_177_lab_green_produces_empty_lab_queue():
    queue = mod.build_audit_queue(lab_green_matrix(), target_environment="LAB", company_id="fenix")
    assert queue == ()


def test_177_lab_green_stays_fully_queued_for_prod():
    queue = mod.build_audit_queue(lab_green_matrix(), target_environment="PROD", company_id="fenix")
    assert len(queue) == 177
    assert all(item["reason"] == "PROMOTION_REQUIRED" for item in queue)


def test_prod_confirmed_operational_is_removed_from_prod_queue():
    rows = tuple({"engine_id": e, "state": "CONFIRMED_OPERATIONAL", "environment": "PROD", "company_id": "fenix"} for e in CANONICAL)
    assert mod.build_audit_queue(rows, target_environment="PROD", company_id="fenix") == ()


def test_other_tenant_record_fails_closed_into_queue():
    row = {"engine_id": CANONICAL[0], "state": "CONFIRMED_OPERATIONAL", "environment": "PROD", "company_id": "other"}
    queue = mod.build_audit_queue((row,), target_environment="PROD", company_id="fenix")
    assert len(queue) == 1
    assert queue[0]["reason"] == "COMPANY_SCOPE_MISMATCH"
