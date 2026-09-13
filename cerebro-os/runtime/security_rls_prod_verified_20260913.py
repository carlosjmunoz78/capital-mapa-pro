from __future__ import annotations

EVIDENCE = {
    "project_ref": "cluhljgonannaafpmblx",
    "migration_name": "enable_rls_four_audited_tables_20260913_retry",
    "migration_applied": True,
    "verified_rls_enabled": {
        "fenix_prod.special_cases": True,
        "fenix_prod.special_case_people": True,
        "fenix_prod.expediente_stage_history": True,
        "fenix_prod.weekly_report_snapshots": True,
    },
    "rows_observed": {
        "fenix_prod.special_cases": 0,
        "fenix_prod.special_case_people": 0,
        "fenix_prod.expediente_stage_history": 24,
        "fenix_prod.weekly_report_snapshots": 1,
    },
    "security_advisor_rls_disabled_present_for_four_targets": False,
    "automatic_privilege_change_allowed": False,
}


def assess() -> dict:
    return {
        **EVIDENCE,
        "four_table_rls_green": all(EVIDENCE["verified_rls_enabled"].values()),
        "security_global_green": False,
        "status": "FOUR_TABLE_RLS_GREEN_SECURITY_REVIEW_CONTINUES",
    }
