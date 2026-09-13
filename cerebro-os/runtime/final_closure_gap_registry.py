from __future__ import annotations

# Canonical fail-closed registry of the remaining global closure gaps.
# This registry does not perform external actions. It exists to prevent false-green
# promotion while evidence is still missing.

GAPS = {
    "SECURITY:supabase_security_review_green": {
        "status": "PARTIAL_HIGH_RISK",
        "blocking": True,
        "required_evidence": (
            "mutator_parity_for_15_authenticated_security_definer_rpcs",
            "caller_and_retirement_evidence_before_any_privilege_change",
            "explicit_human_gate_for_prod_security_change",
        ),
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
            "per_engine_log_coverage",
            "per_engine_metric_coverage",
            "per_engine_incident_coverage",
        ),
    },
    "OBSERVABILITY:monthly_cost_measured": {
        "status": "PARTIAL",
        "blocking": True,
        "required_evidence": (
            "existing_provider_monthly_cost_measurement",
            "engine_or_family_cost_attribution_where_available",
        ),
        "incremental_cerebro_cost_eur": 0.0,
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
