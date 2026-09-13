from __future__ import annotations

AUDIT = {
    "captured_at": "2026-09-13",
    "mode": "READ_ONLY",
    "APP_008_reports": {
        "status": "READ_ONLY_REPORTS_GREEN",
        "edge_function": "fenix-reports-api",
        "edge_active": True,
        "verify_jwt": True,
        "custom_identity_resolution": True,
        "server_rpc": "fenix_prod_reports_server",
        "server_rpc_security_definer": False,
        "direction_only": True,
        "report_items": ("REPORT-PIPELINE", "REPORT-WEEKLY", "REPORT-DAILY"),
        "daily_snapshot_rows": 3,
        "daily_snapshot_rls": True,
        "weekly_snapshot_rows": 1,
        "weekly_snapshot_rls": True,
        "daily_refresh_security_definer": True,
        "weekly_refresh_security_definer": True,
        "send_or_export_mutation_proven": False,
        "ui_shell": "src/InformesShell.tsx",
        "ui_runtime_adapter": "src/reportsRuntime.ts",
        "ui_prod_route": "fenix-reports-api/reports",
        "ui_uses_authenticated_session": True,
        "ui_source_found": True,
        "ui_fails_closed_without_valid_report_url": True,
    },
    "CRM_002_sync": {
        "status": "LEGACY_SYNC_ENDPOINTS_RETIRED_GREEN_FAIL_CLOSED",
        "live_edge_functions": (
            "fenix-crm-sync-once",
            "fenix-crm-sync-trigger-once",
            "fenix-directory-sync-once",
            "fenix-directory-sync-trigger-once",
        ),
        "all_active_but_retired_410": True,
        "retirement_error": "migration_endpoint_retired",
        "verify_jwt": True,
        "legacy_sync_execution_allowed": False,
        "matching_db_rpc_names_present": False,
        "canonical_runtime_should_not_depend_on_legacy_sync": True,
    },
}


def assess() -> dict:
    reports = AUDIT["APP_008_reports"]
    crm = AUDIT["CRM_002_sync"]
    backend_green = all((
        reports["edge_active"],
        reports["verify_jwt"],
        reports["custom_identity_resolution"],
        reports["server_rpc"] == "fenix_prod_reports_server",
        reports["daily_snapshot_rls"],
        reports["weekly_snapshot_rls"],
    ))
    ui_green = all((
        reports["ui_source_found"],
        reports["ui_prod_route"] == "fenix-reports-api/reports",
        reports["ui_uses_authenticated_session"],
        reports["ui_fails_closed_without_valid_report_url"],
    ))
    return {
        "APP_008_backend_green": backend_green,
        "APP_008_ui_green": ui_green,
        "APP_008_green": backend_green and ui_green,
        "CRM_002_legacy_sync_retirement_green": (
            crm["all_active_but_retired_410"]
            and not crm["legacy_sync_execution_allowed"]
            and not crm["matching_db_rpc_names_present"]
        ),
        "safe_to_run_legacy_sync": False,
        "safe_next": "audit_carlos_user_area_and_cerebro_console_gateway",
        "status": "REPORTS_GREEN_CRM_LEGACY_SYNC_RETIRED_GREEN",
    }
