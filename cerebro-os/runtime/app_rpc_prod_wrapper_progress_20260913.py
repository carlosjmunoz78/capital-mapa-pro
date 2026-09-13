from __future__ import annotations

EVIDENCE = {
    "project_ref": "cluhljgonannaafpmblx",
    "authorized_scope": "five_server_only_wrappers_then_gateway_then_live_parity",
    "branch_direct_callers_zero": True,
    "branch_gateway_routes_persisted": True,
    "prod_wrappers": {
        "fenix_prod_notifications_list_server": {
            "exists": True,
            "security_definer": True,
            "execute_roles": ("service_role",),
            "read_only": True,
            "migration": "cerebro_notifications_list_server_20260913",
        },
        "fenix_prod_notification_mark_server": {
            "exists": True,
            "security_definer": True,
            "execute_roles": ("service_role",),
            "migration": "cerebro_notification_mark_server_v2_20260913",
        },
        "fenix_prod_contact_create_server": {
            "exists": True,
            "security_definer": True,
            "execute_roles": ("service_role",),
            "migration": "cerebro_contact_create_server_v2_20260913",
        },
        "fenix_prod_exp_create_server": {
            "exists": True,
            "security_definer": True,
            "execute_roles": ("service_role",),
            "migration": "cerebro_exp_create_server_20260913",
        },
        "fenix_prod_sign_create_server": {
            "exists": True,
            "security_definer": True,
            "execute_roles": ("service_role",),
            "migration": "cerebro_sign_create_server_20260913",
        },
    },
    "gateway_prod_deploy_attempted": True,
    "gateway_prod_deploy_executed": False,
    "gateway_prod_deploy_blocked_by_execution_controls": True,
    "authenticated_execute_revoke_allowed": False,
    "live_parity_proven": False,
    "main_modified": False,
}


def assess() -> dict:
    live = tuple(name for name, row in EVIDENCE["prod_wrappers"].items() if row.get("exists"))
    pending = tuple(name for name, row in EVIDENCE["prod_wrappers"].items() if not row.get("exists"))
    return {
        "live_wrappers": live,
        "pending_wrappers": pending,
        "wrapper_count_live": len(live),
        "wrapper_count_target": 5,
        "status": "FIVE_OF_FIVE_PROD_WRAPPERS_LIVE_GATEWAY_DEPLOY_BLOCKED",
        "authenticated_execute_revoke_allowed": False,
        "live_parity_proven": False,
    }
