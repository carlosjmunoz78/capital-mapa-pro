from __future__ import annotations

EVIDENCE = {
    "human_gate": "APPROVED",
    "project_ref": "cluhljgonannaafpmblx",
    "target": "parallel observability sink outside legacy App/CRM tables",
    "legacy_tables_modified": False,
    "planned_scope": ("company_id", "engine_id", "environment", "version"),
    "planned_kinds": ("log", "metric", "incident"),
    "prod_wiring_attempted": True,
    "prod_wiring_executed": False,
    "blocked_by_execution_controls": True,
    "partial_prod_change_observed": False,
    "additional_subscription_required": False,
    "automatic_prod_promotion_allowed": False,
}


def assess() -> dict:
    return {
        **EVIDENCE,
        "observability_prod_green": False,
        "status": "PROD_WIRING_APPROVED_EXECUTION_BLOCKED_FAIL_CLOSED",
    }
