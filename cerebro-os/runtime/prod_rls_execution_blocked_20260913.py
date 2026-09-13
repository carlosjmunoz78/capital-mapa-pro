from __future__ import annotations

STATE = {
    "human_high_risk_gate_approved": True,
    "isolated_lab_proof_complete": True,
    "isolated_rollback_rehearsal_complete": True,
    "prod_change_attempted": True,
    "execution_tool_blocked": True,
    "prod_change_applied": False,
    "prod_partial_change_detected": False,
    "prod_rollback_required": False,
    "prod_rls_currently_enabled_for_all_four": False,
}


def assess() -> dict:
    return {
        **STATE,
        "security_green": False,
        "promotion_allowed": False,
        "status": "HUMAN_APPROVED_EXECUTION_TOOL_BLOCKED_FAIL_CLOSED",
    }
