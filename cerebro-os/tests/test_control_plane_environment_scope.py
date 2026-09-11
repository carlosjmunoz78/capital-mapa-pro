from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "gateway" / "control_plane.py"

spec = importlib.util.spec_from_file_location("control_plane_environment_scope", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

BASE = dict(route_status="ROUTED", policy_decision="ALLOW", supervisor_state="GREEN", tribunal_approved=True)


def test_lab_green_cannot_authorize_prod_execution():
    result = mod.control_decision(**BASE, promotion_decision="LAB_GREEN", environment="PROD")
    assert result == {"status": "BLOCKED", "reason": "PROMOTION_SCOPE_MISMATCH"}


def test_preprod_green_cannot_authorize_prod_execution():
    result = mod.control_decision(**BASE, promotion_decision="PREPROD_GREEN", environment="PROD")
    assert result["status"] == "BLOCKED"


def test_prod_candidate_is_required_for_prod_control_plane():
    result = mod.control_decision(**BASE, promotion_decision="PROD_CANDIDATE", environment="PROD")
    assert result == {"status": "ALLOW_EXECUTION", "reason": "CONTROL_PLANE_GREEN"}


def test_lab_backwards_default_requires_lab_green():
    result = mod.control_decision(**BASE, promotion_decision="LAB_GREEN")
    assert result["status"] == "ALLOW_EXECUTION"
