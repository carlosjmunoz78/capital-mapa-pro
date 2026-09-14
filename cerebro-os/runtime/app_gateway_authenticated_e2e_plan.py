from __future__ import annotations

# Read-only representation of the live fenix-app-gateway v17 target boundary.
# It does not send HTTP requests and does not contain credentials.

TARGETS = {
    "notifications_list": {
        "method": "GET",
        "path": "/notificaciones?limit=5",
        "write": False,
        "server_rpc": "fenix_prod_notifications_list_server",
        "cleanup_route_proven": True,
    },
    "notification_mark": {
        "method": "POST",
        "path_template": "/notificaciones/{task_id}/state",
        "write": True,
        "server_rpc": "fenix_prod_notification_mark_server",
        "cleanup_route_proven": False,
    },
    "contact_create": {
        "method": "POST",
        "path": "/contactos",
        "write": True,
        "server_rpc": "fenix_prod_contact_create_server",
        "cleanup_route_proven": False,
    },
    "exp_create": {
        "method": "POST",
        "path": "/expedientes",
        "write": True,
        "server_rpc": "fenix_prod_exp_create_server",
        "cleanup_route_proven": False,
    },
    "sign_create": {
        "method": "POST",
        "path": "/firmas",
        "write": True,
        "server_rpc": "fenix_prod_sign_create_server",
        "cleanup_route_proven": False,
    },
}


def assess(*, safe_test_identity_proven: bool = False, high_risk_approved: bool = False) -> dict:
    writes = tuple(name for name, row in TARGETS.items() if row["write"])
    no_cleanup = tuple(
        name for name, row in TARGETS.items() if row["write"] and not row["cleanup_route_proven"]
    )
    read_only = tuple(name for name, row in TARGETS.items() if not row["write"])
    write_execution_allowed = bool(
        safe_test_identity_proven
        and high_risk_approved
        and not no_cleanup
    )
    return {
        "target_count": len(TARGETS),
        "read_only_targets": read_only,
        "write_targets": writes,
        "write_targets_without_proven_cleanup_route": no_cleanup,
        "safe_test_identity_proven": safe_test_identity_proven,
        "high_risk_approved": high_risk_approved,
        "write_execution_allowed": write_execution_allowed,
        "human_required": "HIGH_RISK" if not write_execution_allowed else None,
        "status": "BLOCKED_FAIL_CLOSED" if not write_execution_allowed else "READY_FOR_CONTROLLED_EXECUTION",
    }
