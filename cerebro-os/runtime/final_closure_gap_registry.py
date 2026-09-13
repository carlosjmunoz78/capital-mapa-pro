from __future__ import annotations

# Canonical fail-closed registry of the remaining global closure gaps.
# This registry does not perform external actions. It exists to prevent false-green
# promotion while evidence is still missing.

GAPS = {
    "SECURITY:supabase_security_review_green": {
        "status": "PARTIAL_HIGH_RISK_EXECUTION_BLOCKED",
        "blocking": True,
        "required_evidence": (
            "real_db_mutator_parity_for_15_authenticated_security_definer_rpcs",
            "global_caller_and_retirement_evidence_before_any_privilege_change",
            "real_security_write_path_rollback_evidence",
            "apply_human_approved_four_table_rls_prod_change_when_execution_channel_allows",
        ),
        "human_gate_for_four_table_rls": "APPROVED",
        "automatic_prod_change_allowed": False,
    },
    "RECOVERY:provider_restore_drill_proven": {
        "status": "PENDING_EXTERNAL_PROOF",
        "blocking": True,
        "required_evidence": (
            "isolated_non_prod_restore_target",
            "completed_restore",
            "integrity_check",
            "application_smoke",
            "cleanup_or_retention_evidence",
        ),
        "automatic_prod_restore_allowed": False,
    },
    "RECOVERY:prod_rollback_rehearsal_proven": {
        "status": "PENDING_EXTERNAL_PROOF",
        "blocking": True,
        "required_evidence": (
            "real_release_or_provider_rollback_target",
            "non_destructive_or_preprod_execution",
            "post_rollback_verification",
        ),
        "automatic_prod_rollback_allowed": False,
    },
    "OBSERVABILITY:per_engine_logs_metrics_incidents_complete": {
        "status": "PARTIAL",
        "blocking": True,
        "required_evidence": (
            "parallel_prod_mirroring_wiring_without_legacy_breakage",
            "per_engine_prod_log_coverage",
            "per_engine_prod_metric_coverage",
            "per_engine_prod_incident_coverage",
            "youtube_retained_metric_execution_or_approved_absence_policy",
        ),
        "linkedin_retained_metric_green": True,
        "youtube_reauthorized_and_rewired_green": True,
        "youtube_retained_metric_green": False,
    },
    "FINOPS:monthly_cost_measured": {
        "status": "PARTIAL_AUTHORITATIVE_BILLING_REQUIRED",
        "blocking": True,
        "required_evidence": (
            "notion_exact_monthly_amount_from_authoritative_billing_source",
            "google_cloud_exact_monthly_amount_or_zero_cost_proof_from_authoritative_billing_source",
            "engine_or_family_cost_attribution_where_real_usage_evidence_exists",
        ),
        "incremental_cerebro_cost_eur": 0.0,
        "estimated_amounts_used": False,
    },
}


def assess_final_closure_gaps() -> dict:
    blockers = tuple(name for name, row in GAPS.items() if row.get("blocking"))
    return {
        "gap_count": len(GAPS),
        "blocking_count": len(blockers),
        "blocking": blockers,
        "perfect": not blockers,
        "prod_candidate_allowed": False,
        "prod_green": False,
        "automatic_prod_promotion_allowed": False,
        "status": "FIVE_GLOBAL_GAPS_REMAIN" if blockers else "PROD_CANDIDATE_HUMAN_GATED",
    }
