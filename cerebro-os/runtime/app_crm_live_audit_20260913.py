from __future__ import annotations

AUDIT = {
    "captured_at": "2026-09-13",
    "mode": "READ_ONLY",
    "app_repo": "carlosjmunoz78/fenix-capital-inmo-map",
    "app_default_branch": "main",
    "app_main_sha": "95106d8e792257f809033486b7025d81665ea83b",
    "parallel_branch": "cerebro-app-crm-rpc-migration-v0-20260913",
    "app_repo_modified_by_audit": False,
    "app_preprod_reactivated": False,
    "stack": {"frontend": "React 19 + TypeScript + Vite + React Router", "auth_data": "Supabase", "build": "tsc --noEmit && vite build", "e2e": "Playwright"},
    "auth_and_navigation": {"supabase_session": True, "auth_state_listener": True, "password_recovery": True, "session_context_via_app_gateway": True, "navigation_via_app_gateway": True, "route_access_guard_present": True},
    "prod_gateway": {"slug": "fenix-app-gateway", "active": True, "edge_verify_jwt_flag": False, "custom_bearer_validation_present": True, "custom_identity_uses_auth_get_user": True, "actor_context_resolution_present": True, "service_role_is_server_side": True, "direct_model_access": False},
    "crm_live_tables": {"fenix_prod.clientes": 87, "fenix_prod.inmobiliarias": 401, "fenix_prod.bancos": 6, "fenix_prod.contactos_inmobiliaria": 48, "fenix_prod.contactos_bancarios": 1, "fenix_prod.expediente_personas": 17},
    "crm_read_path": {"contactos_shell_uses_compatibility_adapter": True, "production_adapter_routes_to_app_gateway": True, "production_contact_list_gateway_path": "/contactos", "production_not_notion_runtime": True},
    "security_caller_evidence": {
        "static_audit_ci_green": True,
        "static_audit_run_id": 34774771295,
        "direct_prod_rpc_call_count": 10,
        "unique_direct_prod_rpc_count": 8,
        "direct_prod_rpc_callers_still_exist": True,
        "confirmed_frontend_rpc_callers": (
            "src/ChatShell.tsx -> fenix_prod_chat_list_user", "src/ChatShell.tsx -> fenix_prod_chat_send_user", "src/ContactCreateShell.tsx -> fenix_prod_contact_create", "src/DetailShell.tsx -> fenix_prod_exp_update", "src/ExpedienteCreateShell.tsx -> fenix_prod_exp_create", "src/ExpedienteManualPhaseGuard.tsx -> fenix_prod_exp_update", "src/ExpedienteRenameGuard.tsx -> fenix_prod_exp_update", "src/FirmaCreateShell.tsx -> fenix_prod_sign_create", "src/NotificationsShell.tsx -> fenix_prod_notifications_list_user", "src/NotificationsShell.tsx -> fenix_prod_notification_mark_user",
        ),
        "previous_manual_caller_subset_count": 6,
        "previous_manual_mutating_subset_count": 4,
        "confirmed_server_wrappers": ("fenix_prod_chat_list_server", "fenix_prod_chat_send_server", "fenix_prod_exp_update_server"),
        "missing_server_wrappers": ("fenix_prod_contact_create_server", "fenix_prod_exp_create_server", "fenix_prod_notification_mark_server", "fenix_prod_notifications_list_server", "fenix_prod_sign_create_server"),
        "existing_wrapper_parity_proven_from_function_definition": True,
        "safe_to_revoke_authenticated_execute_now": False,
        "reason": "Static audit found ten live frontend call sites across eight PROD RPCs; five RPCs have no server-only equivalent yet.",
    },
    "crm_runtime": {"crm_sync_once_active": True, "crm_sync_trigger_once_active": True, "directory_sync_active": True, "gateway_active": True},
}


def assess() -> dict:
    app001_green = all((AUDIT["app_main_sha"], AUDIT["app_repo_modified_by_audit"] is False, AUDIT["auth_and_navigation"]["supabase_session"], AUDIT["auth_and_navigation"]["route_access_guard_present"], AUDIT["prod_gateway"]["active"], AUDIT["prod_gateway"]["custom_bearer_validation_present"]))
    crm001_inventory_green = all(v >= 0 for v in AUDIT["crm_live_tables"].values()) and AUDIT["crm_runtime"]["gateway_active"]
    e = AUDIT["security_caller_evidence"]
    return {
        "APP_001_read_only_inventory_green": app001_green,
        "CRM_001_live_inventory_green": crm001_inventory_green,
        "APP_002_OBJ1_caller_inventory_green": e["static_audit_ci_green"] and e["direct_prod_rpc_call_count"] == 10 and e["unique_direct_prod_rpc_count"] == 8,
        "APP_002_existing_server_wrapper_count": len(e["confirmed_server_wrappers"]),
        "APP_002_missing_server_wrapper_count": len(e["missing_server_wrappers"]),
        "APP_002_server_contracts_green": len(e["missing_server_wrappers"]) == 0,
        "security_rpc_retirement_blocked": e["direct_prod_rpc_callers_still_exist"],
        "confirmed_direct_rpc_caller_count": e["previous_manual_caller_subset_count"],
        "confirmed_mutating_direct_rpc_caller_count": e["previous_manual_mutating_subset_count"],
        "exhaustive_static_direct_rpc_call_count": e["direct_prod_rpc_call_count"],
        "exhaustive_static_unique_rpc_count": e["unique_direct_prod_rpc_count"],
        "app_repo_unchanged": not AUDIT["app_repo_modified_by_audit"],
        "app_preprod_stays_cancelled": not AUDIT["app_preprod_reactivated"],
        "ready_for_next_read_only_audit": app001_green and crm001_inventory_green,
        "status": "APP_CRM_CALLER_INVENTORY_GREEN_SERVER_WRAPPERS_PARTIAL" if app001_green and crm001_inventory_green else "APP_CRM_AUDIT_INCOMPLETE",
    }
