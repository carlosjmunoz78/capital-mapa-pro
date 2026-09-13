from __future__ import annotations

# Consolidated, fail-closed caller-discovery matrix.
# It combines already captured read-only evidence only and performs no I/O.

EVIDENCE = {
    "app_current_direct_callers_verified": 6,
    "app_remaining_mutators_zero_indexed_matches": 9,
    "github_repositories_accounted_for": 5,
    "additional_repositories_zero_fenix_prod_prefix_matches": 3,
    "prod_project_edge_surfaces_accounted_for": 38,
    "make_fetched_configuration_fenix_prod_matches": 0,
}

REMAINING_REQUIRED = (
    "real_db_wrapper_replay_for_13_missing_or_non_equivalent_wrappers",
    "write_rollback_evidence_in_isolated_database",
    "caller_migration_or_explicit_keep_and_wrap_cutover_evidence",
    "high_risk_human_gate_before_any_prod_privilege_change",
)


def assess() -> dict:
    return {
        "evidence": dict(EVIDENCE),
        "known_app_direct_callers_preserved": True,
        "negative_searches_treated_as_non_proof_of_global_absence": True,
        "edge_inventory_complete_for_current_prod_project_snapshot": True,
        "repository_inventory_expanded": True,
        "make_negative_evidence_recorded": True,
        "remaining_required": REMAINING_REQUIRED,
        "caller_discovery_internal_inventory_green": True,
        "safe_retirement_proven": False,
        "security_review_green": False,
        "prod_privilege_change_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "status": "CALLER_DISCOVERY_INTERNAL_INVENTORY_GREEN_CUTOVER_AND_DB_REPLAY_PENDING",
    }
