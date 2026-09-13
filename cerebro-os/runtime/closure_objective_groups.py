from __future__ import annotations

# Canonical grouped closure objectives for the final green loop.
# Fail-closed by design: no objective group becomes GREEN from structural proof alone.
# This module performs no external mutation and authorizes no PROD promotion.

OBJECTIVE_GROUPS = {
    "SECURITY": {
        "target": "supabase_security_review_green",
        "status": "PARTIAL_HIGH_RISK",
        "green": False,
        "completed": (
            "15_authenticated_security_definer_rpcs_inventory",
            "15_live_acl_and_definition_fingerprints_captured",
            "33_edge_surfaces_read_only_inspected",
            "6_current_frontend_direct_callers_verified_at_app_head",
            "9_remaining_mutators_frontend_negative_search_recorded_fail_closed",
            "live_implementation_shape_15_of_15_classified",
            "2_direct_server_delegations_identified",
            "15_mutator_8_dimension_parity_matrix_created",
            "13_missing_or_non_equivalent_server_wrapper_contracts_defined",
            "all_mutator_families_semantic_lab_contracts_covered",
            "chat_contacts_exp_create_inmo_followup_lab_replay_green",
            "notifications_profile_socials_profile_update_signature_lab_contracts_green",
            "signature_required_gate_preserved",
            "corrected_frontend_caller_blob_shas_canonicalized",
        ),
        "remaining": (
            "9_mutators_without_current_frontend_direct_caller_proof",
            "13_server_wrapper_real_db_replay_and_tests_in_isolated_non_prod",
            "rollback_evidence_for_security_change_path",
            "caller_migration_and_retirement_evidence_before_any_privilege_change",
            "explicit_high_risk_human_gate_before_prod_security_change",
        ),
    },
    "RECOVERY": {
        "target": "provider_restore_and_prod_rollback_green",
        "status": "PARTIAL_EXTERNAL_PROOF_REQUIRED",
        "green": False,
        "completed": (
            "immutable_git_source_snapshot",
            "runtime_rebuild_rehearsal_ci",
            "non_destructive_rollback_rehearsal_ci",
            "live_supabase_project_and_branch_inventory_captured",
            "legacy_core_preprod_surface_preserved",
            "isolated_restore_plan_defined",
            "unsafe_existing_restore_targets_rejected",
        ),
        "remaining": (
            "isolated_non_prod_restore_target_proven_without_unapproved_cost",
            "completed_provider_restore",
            "restore_integrity_check",
            "application_smoke_after_restore",
            "cleanup_or_retention_evidence",
            "real_release_or_provider_rollback_target_proven",
        ),
    },
    "OBSERVABILITY": {
        "target": "per_engine_logs_metrics_incidents_complete",
        "status": "PARTIAL",
        "green": False,
        "completed": (
            "177_engine_structural_observability_contract",
            "177_engine_lab_log_metric_incident_runtime_proven",
            "shared_scope_fields_company_engine_environment_version",
            "selected_family_live_evidence",
            "prod_live_observability_tables_read_only_verified",
            "prod_current_tables_missing_full_multiempresa_scope_confirmed",
            "parallel_multiempresa_observability_envelope_defined",
            "linkedin_youtube_zero_retained_runs_revalidated_fail_closed",
        ),
        "remaining": (
            "parallel_prod_mirroring_implementation_without_legacy_table_breakage",
            "per_engine_prod_live_log_coverage",
            "per_engine_prod_live_metric_coverage",
            "per_engine_prod_live_incident_coverage",
            "social_linkedin_youtube_retained_metric_execution_or_explicit_approved_absence_policy",
        ),
    },
    "FINOPS": {
        "target": "monthly_cost_measured",
        "status": "PARTIAL",
        "green": False,
        "completed": (
            "supabase_monthly_cost_measured",
            "make_monthly_cost_measured",
            "canva_monthly_cost_measured",
            "hostinger_business_email_monthly_cost_measured",
            "google_cloud_and_notion_billing_email_search_exhausted_without_amount",
            "no_free_tier_overage_claim_without_evidence",
            "incremental_cerebro_cost_target_zero_eur",
        ),
        "remaining": (
            "notion_exact_monthly_amount_from_authoritative_billing_source",
            "google_cloud_exact_monthly_amount_or_zero_cost_proof_from_authoritative_billing_source",
            "engine_or_family_cost_attribution_where_available",
        ),
    },
    "PROMOTION": {
        "target": "prod_candidate_human_gated",
        "status": "BLOCKED_BY_UPSTREAM_GAPS",
        "green": False,
        "completed": (
            "factory_ci_green",
            "177_lab_green_baseline",
            "promotion_gate_fail_closed",
        ),
        "remaining": (
            "security_green",
            "recovery_green",
            "observability_green",
            "finops_green",
            "human_gate_for_final_prod_promotion",
        ),
    },
}

EXECUTION_ORDER = ("SECURITY", "RECOVERY", "OBSERVABILITY", "FINOPS", "PROMOTION")


def assess_objective_groups() -> dict:
    groups = {name: OBJECTIVE_GROUPS[name] for name in EXECUTION_ORDER}
    green = tuple(name for name, row in groups.items() if row["green"])
    pending = tuple(name for name, row in groups.items() if not row["green"])
    return {
        "execution_order": EXECUTION_ORDER,
        "groups": groups,
        "green_groups": green,
        "pending_groups": pending,
        "all_green": not pending,
        "prod_candidate_allowed": False,
        "automatic_prod_promotion_allowed": False,
        "status": "GREEN_LOOP_IN_PROGRESS" if pending else "PROD_CANDIDATE_HUMAN_GATED",
    }
