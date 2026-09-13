from __future__ import annotations

STATE = {
    "captured_at": "2026-09-13",
    "app_repo": "carlosjmunoz78/fenix-capital-inmo-map",
    "parallel_branch": "cerebro-app-crm-rpc-migration-v0-20260913",
    "parallel_head": "17e6d897b56a954e7f61540557812e0d6e3f383e",
    "app_main_unchanged": True,
    "app_preprod_reactivated": False,
    "prod_db_changed_by_this_loop": False,
    "prod_edge_changed_by_this_loop": False,
    "objectives": {
        "OBJ1_DIRECT_CALLER_INVENTORY": "GREEN",
        "OBJ2A_EXISTING_SERVER_WRAPPERS": "GREEN",
        "OBJ2B_FIVE_MISSING_SERVER_WRAPPERS": "DEFINED_NOT_DEPLOYED",
        "OBJ3_GATEWAY_ROUTE_REHEARSAL": "GREEN_RUNNER_ONLY",
        "OBJ4_FRONTEND_MIGRATION_REHEARSAL": "GREEN_RUNNER_ONLY",
        "OBJ5_OLD_NEW_AND_ROLLBACK": "PARTIAL_NEEDS_LIVE_PARITY",
        "OBJ6_RETIRE_AUTHENTICATED_DIRECT_EXECUTE": "BLOCKED_UNTIL_ZERO_LIVE_CALLERS",
    },
    "evidence": {
        "direct_call_count": 10,
        "unique_direct_rpc_count": 8,
        "existing_server_wrappers": 3,
        "missing_server_wrappers": 5,
        "app_branch_build_green": True,
        "app_branch_ci_run": 34775014595,
        "cerebro_ci_prior_green": True,
    },
    "human_gate": {
        "required": True,
        "reason": "HIGH_RISK",
        "scope": "Creating five server-only PROD RPC contracts and deploying controlled gateway/frontend routing changes affects live authentication/write paths.",
        "approved": False,
    },
}


def assess() -> dict:
    pre_gate_green = all((
        STATE["objectives"]["OBJ1_DIRECT_CALLER_INVENTORY"] == "GREEN",
        STATE["objectives"]["OBJ2A_EXISTING_SERVER_WRAPPERS"] == "GREEN",
        STATE["objectives"]["OBJ3_GATEWAY_ROUTE_REHEARSAL"] == "GREEN_RUNNER_ONLY",
        STATE["objectives"]["OBJ4_FRONTEND_MIGRATION_REHEARSAL"] == "GREEN_RUNNER_ONLY",
        STATE["app_main_unchanged"],
        not STATE["app_preprod_reactivated"],
        not STATE["prod_db_changed_by_this_loop"],
        not STATE["prod_edge_changed_by_this_loop"],
    ))
    return {
        "pre_high_risk_gate_green": pre_gate_green,
        "high_risk_gate_required": STATE["human_gate"]["required"],
        "high_risk_gate_approved": STATE["human_gate"]["approved"],
        "live_migration_allowed": pre_gate_green and STATE["human_gate"]["approved"],
        "prod_green": False,
        "status": "PRE_GATE_GREEN_HIGH_RISK_APPROVAL_REQUIRED" if pre_gate_green else "PRE_GATE_INCOMPLETE",
    }
