from __future__ import annotations

# Evidence for the temporary isolated Supabase branch attempt used to unblock
# RECOVERY/SECURITY without touching PROD. The branch was removed after the
# provider reported MIGRATIONS_FAILED and the preview contained no public tables.

ATTEMPT = {
    "branch_name": "cerebro-recovery-security-lab-20260913",
    "branch_id": "eb38ac6b-15a1-4d36-9e96-6911da787d50",
    "project_ref": "nwottgkdqfdgwgkwfgkw",
    "parent_project_ref": "cluhljgonannaafpmblx",
    "hourly_cost": 0.01344,
    "with_data": False,
    "provider_status": "MIGRATIONS_FAILED",
    "preview_project_status": "ACTIVE_HEALTHY",
    "public_table_count_observed": 0,
    "last_applied_migration_version": "20260903190642",
    "last_applied_migration_name": "secure_internal_chat_authenticated_rpcs",
    "deleted_after_failure": True,
    "prod_mutation_performed": False,
    "legacy_project_mutation_performed": False,
}


def assess() -> dict:
    failed = ATTEMPT["provider_status"] == "MIGRATIONS_FAILED"
    unusable = failed or ATTEMPT["public_table_count_observed"] == 0
    return {
        "attempted_isolated_branch": True,
        "provider_migration_failed": failed,
        "usable_restore_target": not unusable,
        "real_prod_data_restore_proven": False,
        "real_security_db_replay_proven": False,
        "cost_stopped_after_failure": ATTEMPT["deleted_after_failure"],
        "prod_preserved": not ATTEMPT["prod_mutation_performed"],
        "legacy_preserved": not ATTEMPT["legacy_project_mutation_performed"],
        "next_gate": "FIND_ZERO_OR_EXISTING_SAFE_RESTORE_PATH_OR_PROVIDER_RESTORE_MECHANISM_WITH_DATA",
        "status": "PAID_BRANCH_ATTEMPT_FAILED_CLEANED_UP_FAIL_CLOSED",
    }
