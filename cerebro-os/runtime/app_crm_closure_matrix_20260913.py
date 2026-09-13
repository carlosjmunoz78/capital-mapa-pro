from __future__ import annotations

OBJECTIVES = {
    "APP_001_inventory": "GREEN",
    "CRM_001_inventory": "GREEN",
    "APP_002_auth_rpc_security": "PARTIAL_LIVE_WRAPPERS_BLOCKED",
    "APP_003_expedientes": "GREEN_READ_ONLY_WITH_RPC_MIGRATION_SUBGAP",
    "APP_004_tasks_notifications": "GREEN_READ_ONLY_WITH_NOTIFICATION_GATEWAY_SUBGAP",
    "APP_005_documents": "GREEN",
    "APP_006_signatures": "GREEN_READ_ONLY_WITH_CREATE_GATEWAY_SUBGAP",
    "APP_007_communications": "PARTIAL_PROD_ENDPOINT_MISMATCH",
    "APP_008_reports": "GREEN",
    "CRM_002_sync_consistency": "GREEN_LEGACY_SYNC_RETIRED_FAIL_CLOSED",
    "APP_009_carlos_cerebro_access": "PARTIAL_WEB_ROUTE_GREEN_PROFILE_LINK_GATED",
    "APP_010_cerebro_gateway": "PARTIAL_HTTP_AND_WEB_UI_GREEN_DEPLOYED_URL_MISSING",
    "APP_011_old_new_rollback_promotion": "BLOCKED_UPSTREAM_AND_HUMAN_GATE",
}

BLOCKERS = {
    "rpc_live_migration": {
        "authorized": True,
        "remaining_server_wrappers": 5,
        "runner_direct_callers_before": 10,
        "runner_direct_callers_after": 0,
        "persisted_branch_direct_callers_zero": True,
        "live_direct_callers_zero_proven": False,
        "live_parity_proven": False,
        "authenticated_execute_revoke_allowed": False,
        "execution_channel_blocked_prior_attempts": True,
        "branch_persisted_migrations": {
            "notifications_list": True,
            "notification_mark": True,
            "signature_create": True,
            "branch_head": "4a4036991e33614085a62b705bb9714b6065b6bd",
            "audit_ci_run": 34786000611,
            "audit_ci_success": True,
            "main_modified": False,
            "prod_rpc_permissions_modified": False,
        },
    },
    "communications": {
        "prod_gateway_exists": True,
        "app_shell_targets_test_gateway": True,
        "test_gateway_present_in_current_prod_edge_inventory": False,
        "real_send_claimed": False,
    },
    "cerebro_console": {
        "logical_gateway_contract_green": True,
        "http_surface_green": True,
        "pipeline_audit_path_green": True,
        "trusted_upstream_identity_boundary_green": True,
        "browser_identity_header_trusted": False,
        "app_profile_surface_found": True,
        "internal_console_route_present": True,
        "internal_console_route": "/cerebro",
        "web_shell_fail_closed_without_gateway_url": True,
        "deployed_authenticated_console_url_proven": False,
        "carlos_profile_link_present": False,
        "dead_link_allowed": False,
    },
    "global_pre_app_closure": {
        "security_global_green": False,
        "recovery_global_green": False,
        "observability_global_green": False,
        "finops_global_green": False,
        "promotion_human_gate_required": True,
    },
}


def assess() -> dict:
    fully_green = tuple(k for k, v in OBJECTIVES.items() if v == "GREEN" or v.startswith("GREEN_"))
    pending = tuple(k for k, v in OBJECTIVES.items() if not (v == "GREEN" or v.startswith("GREEN_")))
    return {
        "green_objectives": fully_green,
        "pending_objectives": pending,
        "app_main_mutation_claimed": False,
        "app_preprod_reactivated": False,
        "global_prod_green": False,
        "automatic_prod_promotion_allowed": False,
        "status": "APP_CRM_INCREMENTAL_CLOSURE_CONTINUES_FAIL_CLOSED",
    }
