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
            "33_edge_surfaces_read_only_inspected",
            "6_current_frontend_direct_callers_verified_at_app_head",
            "signature_required_gate_preserved",
            "corrected_frontend_caller_blob_shas_canonicalized",
        ),
        "remaining": (
            "9_mutators_without_current_frontend_direct_caller_proof",
            "mutator_family_parity_complete",
            "caller_retirement_evidence_before_any_privilege_change",
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
            "legacy_core_preprod_surface_preserved",
            "isolated_restore_plan_defined",
        ),
        "remaining": (
            "isolated_non_prod_restore_target_proven",
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
            "shared_scope_fields_company_engine_environment_version",
            "selected_family_live_evidence",
        ),
        "remaining": (
            "per_engine_live_log_coverage",
            "per_engine_live_metric_coverage",
            "per_engine_live_incident_coverage",
            "social_linkedin_youtube_retained_metric_execution",
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
            "incremental_cerebro_cost_target_zero_eur",
        ),
        "remaining": (
            "notion_exact_monthly_amount",
            "google_cloud_exact_monthly_amount_or_zero_cost_proof",
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
