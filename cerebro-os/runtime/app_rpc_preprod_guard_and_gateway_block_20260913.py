from __future__ import annotations

CUT = {
    "app_branch": {
        "head": "03ccd33986b663d8ca4080a6941e63ed429141a0",
        "direct_prod_rpc_callers": 0,
        "audit_ci_green": True,
        "preprod_app_build_manual_only": True,
        "cerebro_factory_preprod_manual_only": True,
        "pr_376_open": True,
        "pr_376_draft": True,
        "pr_376_merged": False,
    },
    "rpc_parity": {
        "safe_live_checks": 8,
        "all_exact_equal": True,
        "all_non_mutating": True,
        "successful_write_path_parity_proven": False,
        "gateway_end_to_end_parity_proven": False,
    },
    "gateway_prod": {
        "live_version": 16,
        "new_routes_deploy_authorized": True,
        "new_routes_deploy_attempted": True,
        "new_routes_deploy_executed": False,
        "blocked_by_execution_controls": True,
        "partial_change_observed": False,
    },
    "security": {
        "authenticated_execute_revoke_allowed": False,
        "final_prod_promotion_allowed": False,
    },
}


def assess() -> dict:
    return {
        "preprod_auto_trigger_guard_green": (
            CUT["app_branch"]["preprod_app_build_manual_only"]
            and CUT["app_branch"]["cerebro_factory_preprod_manual_only"]
        ),
        "branch_rpc_migration_green": (
            CUT["app_branch"]["direct_prod_rpc_callers"] == 0
            and CUT["app_branch"]["audit_ci_green"]
        ),
        "safe_live_parity_green": (
            CUT["rpc_parity"]["all_exact_equal"]
            and CUT["rpc_parity"]["all_non_mutating"]
        ),
        "gateway_prod_green": CUT["gateway_prod"]["new_routes_deploy_executed"],
        "global_rpc_cutover_green": False,
        "status": "APP_RPC_CUTOVER_FAIL_CLOSED_GATEWAY_DEPLOY_PENDING",
    }
