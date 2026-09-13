from __future__ import annotations

BLOCK_GROUPS = {
    "STRUCTURAL": {
        "engine_registry_177_lab_green": True,
        "make_inventory_closed": True,
        "factory_legacy_green_code_ci": True,
        "core_replay_green_code_ci": True,
        "identity_credentials_policy_green": True,
        "console_gateway_green_code_ci": True,
        "dependency_live_verified": True,
    },
    "SECURITY": {
        "supabase_security_review_green": False,
    },
    "RECOVERY": {
        "source_backup_proven": False,
        "provider_restore_drill_proven": False,
        "prod_rollback_rehearsal_proven": False,
    },
    "OBSERVABILITY": {
        "per_engine_logs_metrics_incidents_complete": False,
        "monthly_cost_measured": False,
    },
}

NON_BLOCKING = {"tiktok": "PARKED_ACCOUNT_NOT_AVAILABLE"}


def assess_master_closure() -> dict:
    pending = tuple(
        f"{group}:{check}"
        for group, checks in BLOCK_GROUPS.items()
        for check, green in checks.items()
        if not green
    )
    structural_green = all(BLOCK_GROUPS["STRUCTURAL"].values())
    perfect = not pending
    return {
        "structural_green": structural_green,
        "pending": pending,
        "perfect": perfect,
        "prod_candidate": perfect,
        "prod_green": False,
        "automatic_prod_promotion_allowed": False,
        "prod_mutation_allowed": False,
        "non_blocking": dict(NON_BLOCKING),
        "next_groups": tuple(group for group in ("SECURITY", "RECOVERY", "OBSERVABILITY") if not all(BLOCK_GROUPS[group].values())),
        "status": "PERFECT_PENDING_EXTERNAL_EVIDENCE" if pending else "PROD_CANDIDATE_HUMAN_GATED",
    }
