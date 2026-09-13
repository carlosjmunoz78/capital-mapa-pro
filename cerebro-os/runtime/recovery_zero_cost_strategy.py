from __future__ import annotations

COMPANY_ID = "fenix_capital"
ENVIRONMENT = "PROD"


def assess_zero_cost_recovery_strategy() -> dict:
    """Fail-closed recovery strategy that preserves the 0 EUR additional-cost principle.

    A paid Supabase preview branch is not required by default. Existing resources and
    deterministic rehearsal evidence are preferred. Provider restore stays unproven
    until an isolated restore can be demonstrated without mutating PROD.
    """
    return {
        "company_id": COMPANY_ID,
        "environment": ENVIRONMENT,
        "new_paid_branch_required": False,
        "paid_branch_created": False,
        "incremental_monthly_cost_eur": 0.0,
        "source_snapshot_proven": True,
        "runtime_rebuild_proven": True,
        "runtime_rollback_rehearsal_proven": True,
        "provider_restore_proven": False,
        "prod_database_restore_allowed": False,
        "prod_destructive_test_allowed": False,
        "preferred_restore_target": "EXISTING_NON_PROD_OR_PROVIDER_NATIVE_TEMP_RESTORE",
        "fallback_paid_branch": "MONEY_LIMIT_HUMAN_CONFIRMATION_REQUIRED",
        "human_reason_if_paid_resource_needed": "MONEY_LIMIT",
        "status": "ZERO_COST_PATH_ACTIVE_PROVIDER_RESTORE_PENDING",
    }
