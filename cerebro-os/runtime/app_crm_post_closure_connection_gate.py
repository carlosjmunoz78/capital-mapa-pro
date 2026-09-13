from __future__ import annotations

# App/CRM connection is deliberately sequenced AFTER global closure.
# The App itself does not regain a PREPROD deployment. Technical LAB/PREPROD
# may still be used for isolated engine/recovery validation outside the App.

REQUIRED_GLOBAL_GAPS = (
    "SECURITY:supabase_security_review_green",
    "RECOVERY:provider_restore_drill_proven",
    "RECOVERY:prod_rollback_rehearsal_proven",
    "OBSERVABILITY:per_engine_logs_metrics_incidents_complete",
    "OBSERVABILITY:monthly_cost_measured",
)

CONNECTION_POLICY = {
    "app_preprod_reactivated": False,
    "connect_after_global_closure": True,
    "gateway_required": True,
    "direct_model_connection_allowed": False,
    "direct_uncontrolled_table_write_allowed": False,
    "preserve_existing_app": True,
    "preserve_existing_crm": True,
    "preserve_existing_supabase_contracts": True,
    "old_vs_new_required_where_behavior_changes": True,
    "rollback_required": True,
    "gradual_promotion_required": True,
}


def assess_app_crm_connection(global_gap_status: dict[str, bool]) -> dict:
    missing = tuple(name for name in REQUIRED_GLOBAL_GAPS if not global_gap_status.get(name, False))
    ready = not missing
    return {
        "required_global_gaps": REQUIRED_GLOBAL_GAPS,
        "missing_green_evidence": missing,
        "global_closure_green": ready,
        "app_crm_connection_allowed": ready,
        "app_preprod_reactivated": False,
        "gateway_required": True,
        "direct_model_connection_allowed": False,
        "direct_uncontrolled_table_write_allowed": False,
        "prod_mutation_allowed": False,
        "human_gates_still_apply": True,
        "policy": dict(CONNECTION_POLICY),
        "status": "APP_CRM_CONNECTION_READY_HUMAN_GATED" if ready else "APP_CRM_CONNECTION_BLOCKED_UNTIL_GLOBAL_CLOSURE",
    }
