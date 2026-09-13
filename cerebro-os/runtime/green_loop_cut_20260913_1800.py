from __future__ import annotations

# Evidence-only cut of the 2026-09-13 18:00 Europe/Madrid green loop.
# It authorizes no PROD mutation and preserves fail-closed promotion gates.

CUT = {
    "factory_ci": "GREEN",
    "youtube_retained_health": {
        "green": True,
        "execution_id": "8748fa64f694410e845bd220ab223733",
        "status": "success",
        "operations": 3,
        "scenario_returned_inactive": True,
    },
    "security_four_table_rls": {
        "human_gate": "APPROVED",
        "lab_and_rollback_rehearsal": True,
        "prod_apply_attempted_again": True,
        "prod_apply_executed": False,
        "blocked_by_execution_controls": True,
        "partial_prod_change_observed": False,
        "prod_migration_present": False,
    },
    "recovery": {
        "prod_branch_count": 1,
        "prod_only_default_main": True,
        "legacy_branch_count": 0,
        "isolated_restore_target_available": False,
        "restore_project_allowed_now": False,
        "branch_cost_lookup_requires_user_supplied_organization_id": True,
    },
    "finops": {
        "notion_billing_search_revalidated": True,
        "notion_exact_amount_found": False,
        "notion_invoice_attachment_found": False,
        "google_cloud_billing_search_revalidated": True,
        "google_cloud_exact_amount_found": False,
        "google_cloud_invoice_attachment_found": False,
        "estimated_amounts_used": False,
    },
}


def assess() -> dict:
    return {
        "youtube_green": CUT["youtube_retained_health"]["green"],
        "security_prod_rls_green": CUT["security_four_table_rls"]["prod_apply_executed"],
        "recovery_green": CUT["recovery"]["isolated_restore_target_available"],
        "finops_green": CUT["finops"]["notion_exact_amount_found"] and CUT["finops"]["google_cloud_exact_amount_found"],
        "automatic_prod_promotion_allowed": False,
        "status": "GREEN_LOOP_IN_PROGRESS",
    }
