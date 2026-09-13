from __future__ import annotations

AUDIT = {
    "captured_at": "2026-09-13",
    "mode": "READ_ONLY",
    "app_repo": "carlosjmunoz78/fenix-capital-inmo-map",
    "app_default_branch": "main",
    "app_main_sha": "95106d8e792257f809033486b7025d81665ea83b",
    "app_repo_modified_by_audit": False,
    "app_preprod_reactivated": False,
    "stack": {
        "frontend": "React 19 + TypeScript + Vite + React Router",
        "auth_data": "Supabase",
        "build": "tsc --noEmit && vite build",
        "e2e": "Playwright",
    },
    "auth_and_navigation": {
        "supabase_session": True,
        "auth_state_listener": True,
        "password_recovery": True,
        "session_context_via_app_gateway": True,
        "navigation_via_app_gateway": True,
        "route_access_guard_present": True,
    },
    "prod_gateway": {
        "slug": "fenix-app-gateway",
        "active": True,
        "edge_verify_jwt_flag": False,
        "custom_bearer_validation_present": True,
        "custom_identity_uses_auth_get_user": True,
        "actor_context_resolution_present": True,
        "service_role_is_server_side": True,
        "direct_model_access": False,
    },
    "crm_live_tables": {
        "fenix_prod.clientes": 87,
        "fenix_prod.inmobiliarias": 401,
        "fenix_prod.bancos": 6,
        "fenix_prod.contactos_inmobiliaria": 48,
        "fenix_prod.contactos_bancarios": 1,
        "fenix_prod.expediente_personas": 17,
    },
    "crm_read_path": {
        "contactos_shell_uses_compatibility_adapter": True,
        "production_adapter_routes_to_app_gateway": True,
        "production_contact_list_gateway_path": "/contactos",
        "production_not_notional_runtime": True,
    },
    "security_caller_evidence": {
        "direct_prod_rpc_callers_still_exist": True,
        "confirmed_frontend_rpc_callers": (
            "src/ContactCreateShell.tsx -> fenix_prod_contact_create",
            "src/ExpedienteCreateShell.tsx -> fenix_prod_exp_create",
            "src/ChatShell.tsx -> fenix_prod_chat_list_user",
            "src/ChatShell.tsx -> fenix_prod_chat_send_user",
            "src/NotificationsShell.tsx -> fenix_prod_notifications_list_user",
            "src/NotificationsShell.tsx -> fenix_prod_notification_mark_user",
        ),
        "confirmed_mutating_security_definer_callers": (
            "fenix_prod_contact_create",
            "fenix_prod_exp_create",
            "fenix_prod_chat_send_user",
            "fenix_prod_notification_mark_user",
        ),
        "safe_to_revoke_authenticated_execute_now": False,
        "reason": "Live frontend callers still invoke authenticated SECURITY DEFINER RPCs directly in PROD.",
    },
    "crm_runtime": {
        "crm_sync_once_active": True,
        "crm_sync_trigger_once_active": True,
        "directory_sync_active": True,
        "gateway_active": True,
    },
}


def assess() -> dict:
    app001_green = all((
        AUDIT["app_main_sha"],
        AUDIT["app_repo_modified_by_audit"] is False,
        AUDIT["auth_and_navigation"]["supabase_session"],
        AUDIT["auth_and_navigation"]["route_access_guard_present"],
        AUDIT["prod_gateway"]["active"],
        AUDIT["prod_gateway"]["custom_bearer_validation_present"],
    ))
    crm001_inventory_green = all(v >= 0 for v in AUDIT["crm_live_tables"].values()) and AUDIT["crm_runtime"]["gateway_active"]
    security_retirement_blocked = AUDIT["security_caller_evidence"]["direct_prod_rpc_callers_still_exist"]
    return {
        "APP_001_read_only_inventory_green": app001_green,
        "CRM_001_live_inventory_green": crm001_inventory_green,
        "security_rpc_retirement_blocked": security_retirement_blocked,
        "confirmed_direct_rpc_caller_count": len(AUDIT["security_caller_evidence"]["confirmed_frontend_rpc_callers"]),
        "confirmed_mutating_direct_rpc_caller_count": len(AUDIT["security_caller_evidence"]["confirmed_mutating_security_definer_callers"]),
        "app_repo_unchanged": not AUDIT["app_repo_modified_by_audit"],
        "app_preprod_stays_cancelled": not AUDIT["app_preprod_reactivated"],
        "ready_for_next_read_only_audit": app001_green and crm001_inventory_green,
        "status": "APP_CRM_AUDIT_BASELINE_GREEN_WITH_SECURITY_CALLER_BLOCK" if app001_green and crm001_inventory_green else "APP_CRM_AUDIT_INCOMPLETE",
    }
