from __future__ import annotations

CUT = {
    "cut_at": "2026-09-14T07:04:00+02:00",
    "app_prod": {
        "main_sha": "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c",
        "prod_live_deploy_run": 34790008072,
        "prod_live_deploy_green": True,
        "prod_runtime_smoke_run": 34790008059,
        "prod_runtime_smoke_green": True,
        "live_exact_sha_green": True,
        "prod_only_backend_binding_green": True,
        "gateway_health_green": True,
        "anonymous_gateway_fail_closed_green": True,
    },
    "security": {
        "status": "PARTIAL_AUTHENTICATED_HTTP_E2E_HIGH_RISK_GATE",
        "green": False,
        "source_promotion_green": True,
        "target_callers_zero_green": True,
        "advisor_observed_at": "2026-09-14T05:04:48Z",
        "rls_no_policy_info_count": 44,
        "security_definer_authenticated_warn_count": 24,
        "pg_net_public_warn_count": 1,
        "leaked_password_protection_warn_count": 1,
        "cloudflare_pages_failure_blocks_app_runtime": False,
        "cloudflare_pages_resource_mutation_allowed": False,
        "authenticated_http_e2e_green": False,
        "http_write_rollback_green": False,
        "legacy_execute_retirement_allowed": False,
        "human_required": "HIGH_RISK",
    },
    "recovery": {
        "status": "PARTIAL_REAL_ROLLBACK_CANDIDATE_AND_NON_MUTATING_REHEARSAL_WORKFLOW_FOUND",
        "green": False,
        "previous_prod_source_sha": "c7a15cff9a387f1f142c8eeb06fd83a799e85a61",
        "previous_prod_source_resolves": True,
        "rollback_rehearsal_workflow_present": True,
        "rollback_rehearsal_is_non_mutating": True,
        "historical_workflow_dispatch_runs": 0,
        "old_sha_rehearsal_green": False,
        "provider_restore_green": False,
        "paid_restore_resource_created": False,
    },
    "observability": {
        "status": "PARTIAL_ZERO_COST_LAB_GREEN_PERSISTENT_PROD_SINK_OPEN",
        "green": False,
        "lab_177_green": True,
        "zero_cost_jsonl_green": True,
        "persistent_prod_aux_sink_green": False,
    },
    "finops": {
        "status": "PARTIAL_CURRENT_REFERENCE_FOUND_EXACT_INVOICES_OPEN",
        "green": False,
        "notion_current_reference_found": True,
        "notion_reference_usd_per_member_month": 20,
        "notion_reference_plan_label": "Business",
        "notion_reference_state": "En progreso",
        "notion_exact_current_invoice_eur_green": False,
        "google_cloud_payment_issue_evidence_found": True,
        "google_cloud_exact_monthly_amount_green": False,
        "estimated_unknown_costs_allowed": False,
    },
    "promotion": {
        "status": "BLOCKED_BY_UPSTREAM_GAPS_AND_FINAL_HUMAN_GATE",
        "green": False,
        "automatic_prod_promotion_allowed": False,
    },
}


def assess() -> dict:
    grouped = ("security", "recovery", "observability", "finops", "promotion")
    pending = tuple(name for name in grouped if not CUT[name]["green"])
    return {
        "groups": grouped,
        "pending": pending,
        "all_green": not pending,
        "automatic_prod_promotion_allowed": False,
        "status": "GREEN_LOOP_IN_PROGRESS" if pending else "PROD_CANDIDATE_HUMAN_GATED",
    }
