from __future__ import annotations

BLOCKING_EVIDENCE = {
    "dependency_live_verification": ("app", "crm", "supabase", "notion", "wordpress"),
    "security_review": ("supabase_rls", "security_definer_privileges", "extension_location", "leaked_password_protection"),
    "recovery_external_proof": ("source_backup", "provider_restore", "prod_rollback_rehearsal"),
    "observability_per_engine": ("logs", "metrics", "incidents", "cost_measured"),
}

NON_BLOCKING_PARKED = {
    "tiktok": "ACCOUNT_NOT_AVAILABLE",
}

GREEN_STRUCTURAL = (
    "engine_registry_177_lab_green",
    "make_prod_inventory",
    "make_test_inventory",
    "make_core_inventory",
    "factory_legacy_contracts",
    "core_specific_replay_contracts",
    "human_exception_policy",
    "promotion_gate_code",
)


def assess_rollup(
    *,
    dependency_live_green: bool,
    security_review_green: bool = False,
    recovery_external_green: bool,
    observability_green: bool,
) -> dict:
    blockers = []
    if not dependency_live_green:
        blockers.append("dependency_live_verification")
    if not security_review_green:
        blockers.append("security_review")
    if not recovery_external_green:
        blockers.append("recovery_external_proof")
    if not observability_green:
        blockers.append("observability_per_engine")
    prod_candidate = not blockers
    return {
        "green_structural": GREEN_STRUCTURAL,
        "dependency_live_verified": dependency_live_green,
        "security_review_green": security_review_green,
        "blocking_evidence": tuple(blockers),
        "blocking_detail": {name: BLOCKING_EVIDENCE[name] for name in blockers},
        "non_blocking_parked": dict(NON_BLOCKING_PARKED),
        "prod_candidate": prod_candidate,
        "prod_green": False,
        "automatic_prod_promotion_allowed": False,
        "external_mutation_allowed": False,
        "next_action": "GRADUAL_HUMAN_GATED_PROMOTION" if prod_candidate else "COLLECT_EXTERNAL_EVIDENCE",
    }
