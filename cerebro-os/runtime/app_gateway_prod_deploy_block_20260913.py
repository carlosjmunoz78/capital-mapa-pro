from __future__ import annotations

EVIDENCE = {
    "project_ref": "cluhljgonannaafpmblx",
    "gateway": "fenix-app-gateway",
    "current_version": 16,
    "current_status": "ACTIVE",
    "target_routes_persisted_in_app_branch": True,
    "prod_deploy_attempted": True,
    "prod_deploy_executed": False,
    "canary_deploy_attempted": True,
    "canary_deploy_executed": False,
    "blocked_by_execution_controls": True,
    "partial_change_observed": False,
    "five_server_wrappers_live": True,
    "branch_direct_callers_zero": True,
    "live_gateway_parity_proven": False,
    "authenticated_execute_revoke_allowed": False,
}


def assess() -> dict:
    return {
        "gateway_live_new_routes": False,
        "live_parity_proven": False,
        "authenticated_execute_revoke_allowed": False,
        "status": "GATEWAY_DEPLOY_BLOCKED_FAIL_CLOSED",
    }
