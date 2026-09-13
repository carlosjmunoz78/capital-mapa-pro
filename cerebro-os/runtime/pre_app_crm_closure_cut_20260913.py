from __future__ import annotations

CUT = {
    "security": {
        "four_table_rls_prod_green": True,
        "remaining": (
            "real_db_mutator_parity_for_authenticated_security_definer_rpcs",
            "global_caller_retirement_evidence_before_privilege_change",
            "real_security_write_path_rollback_evidence",
        ),
    },
    "recovery": {
        "temporary_branch_create_delete_proven": True,
        "schema_only_branch_not_provider_restore": True,
        "remaining": (
            "true_provider_restore_or_clone_with_data",
            "integrity_check",
            "application_smoke",
            "cleanup_evidence",
            "real_provider_or_release_rollback_target",
        ),
    },
    "observability": {
        "youtube_retained_health_green": True,
        "linkedin_retained_health_green": True,
        "seo_retained_health_green": True,
        "remaining": (
            "parallel_prod_mirroring_wiring_without_legacy_breakage",
            "per_engine_prod_log_coverage",
            "per_engine_prod_metric_coverage",
            "per_engine_prod_incident_coverage",
            "seo_prod_incident_capture_evidence_after_safe_wiring",
        ),
    },
    "finops": {
        "known_provider_costs_are_evidenced": True,
        "estimated_amounts_used": False,
        "remaining": (
            "notion_exact_monthly_amount_from_authoritative_billing_source",
            "google_cloud_exact_monthly_amount_or_zero_cost_proof_from_authoritative_billing_source",
        ),
    },
    "promotion": {
        "automatic_prod_promotion_allowed": False,
        "remaining": ("all_upstream_green", "final_human_gate"),
    },
}


def assess() -> dict:
    pending = tuple(name for name, row in CUT.items() if row.get("remaining"))
    return {
        "pending_groups": pending,
        "ready_to_enter_app_crm_without_claiming_global_prod_green": True,
        "global_prod_green": False,
        "automatic_prod_promotion_allowed": False,
        "status": "PRE_APP_CRM_CLOSURE_IN_PROGRESS",
    }
