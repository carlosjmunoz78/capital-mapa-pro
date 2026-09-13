from __future__ import annotations

AUDIT = {
    "captured_at": "2026-09-13",
    "mode": "READ_ONLY",
    "APP_008_reports": {
        "status": "BACKEND_GREEN_UI_WIRING_POR_AUDITAR",
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
        "indexed_main_ui_source_found": False,
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
    return {
        "APP_008_backend_green": all((
            reports["edge_active"],
            reports["verify_jwt"],
            reports["custom_identity_resolution"],
            reports["server_rpc"] == "fenix_prod_reports_server",
            reports["daily_snapshot_rls"],
            reports["weekly_snapshot_rls"],
        )),
        "APP_008_ui_green": reports["indexed_main_ui_source_found"],
        "CRM_002_legacy_sync_retirement_green": (
            crm["all_active_but_retired_410"]
            and not crm["legacy_sync_execution_allowed"]
            and not crm["matching_db_rpc_names_present"]
        ),
        "safe_to_run_legacy_sync": False,
        "safe_next": "audit_carlos_user_area_and_cerebro_console_gateway",
        "status": "REPORTS_BACKEND_GREEN_CRM_LEGACY_SYNC_RETIRED_UI_POR_AUDITAR",
    }
