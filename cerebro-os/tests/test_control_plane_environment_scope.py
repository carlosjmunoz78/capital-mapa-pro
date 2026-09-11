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

EVIDENCE = {
    "route": "evidence:route",
    "policy": "evidence:policy",
    "supervisor": "evidence:supervisor",
    "tribunal": "evidence:tribunal",
    "promotion": "evidence:promotion",
}
BASE = dict(route_status="ROUTED", policy_decision="ALLOW", supervisor_state="GREEN", tribunal_approved=True)


def test_lab_green_cannot_authorize_prod_execution():
    result = mod.control_decision(**BASE, promotion_decision="LAB_GREEN", environment="PROD", evidence_refs=EVIDENCE)
    assert result == {"status": "BLOCKED", "reason": "PROMOTION_SCOPE_MISMATCH"}


def test_preprod_green_cannot_authorize_prod_execution():
    result = mod.control_decision(**BASE, promotion_decision="PREPROD_GREEN", environment="PROD", evidence_refs=EVIDENCE)
    assert result["status"] == "BLOCKED"


def test_prod_candidate_requires_evidence_for_prod_control_plane():
    missing = mod.control_decision(**BASE, promotion_decision="PROD_CANDIDATE", environment="PROD")
    assert missing["status"] == "BLOCKED"
    assert missing["reason"] == "EVIDENCE_MISSING"
    assert set(missing["missing"]) == set(EVIDENCE)

    result = mod.control_decision(**BASE, promotion_decision="PROD_CANDIDATE", environment="PROD", evidence_refs=EVIDENCE)
    assert result == {"status": "ALLOW_EXECUTION", "reason": "CONTROL_PLANE_GREEN"}


def test_lab_default_also_requires_lab_green_and_evidence():
    without_evidence = mod.control_decision(**BASE, promotion_decision="LAB_GREEN")
    assert without_evidence["status"] == "BLOCKED"
    assert without_evidence["reason"] == "EVIDENCE_MISSING"

    result = mod.control_decision(**BASE, promotion_decision="LAB_GREEN", evidence_refs=EVIDENCE)
    assert result["status"] == "ALLOW_EXECUTION"
