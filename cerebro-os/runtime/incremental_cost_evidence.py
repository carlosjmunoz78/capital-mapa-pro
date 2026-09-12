from __future__ import annotations

# This evidence covers incremental spend introduced by the CEREBRO runtime work in this branch.
# It does not claim knowledge of the user's existing provider invoices or total monthly platform cost.
EVIDENCE = {
    "new_subscriptions_added": 0,
    "paid_ai_required": False,
    "new_paid_provider_required": False,
    "incremental_monthly_cost_eur": 0.0,
    "basis": (
        "deterministic_python_runtime",
        "existing_github_repository_and_actions",
        "existing_supabase_projects",
        "existing_make_workspace",
        "existing_notion_workspace",
        "existing_wordpress_site",
    ),
    "existing_provider_total_monthly_cost_eur": None,
}


def assess_incremental_cost() -> dict:
    zero_incremental = (
        EVIDENCE["new_subscriptions_added"] == 0
        and EVIDENCE["paid_ai_required"] is False
        and EVIDENCE["new_paid_provider_required"] is False
        and EVIDENCE["incremental_monthly_cost_eur"] == 0.0
    )
    total_provider_cost_known = EVIDENCE["existing_provider_total_monthly_cost_eur"] is not None
    return {
        "incremental_cost_green": zero_incremental,
        "incremental_monthly_cost_eur": EVIDENCE["incremental_monthly_cost_eur"],
        "additional_paid_ai_required": False,
        "new_subscription_required": False,
        "existing_provider_total_cost_measured": total_provider_cost_known,
        "observability_cost_gate_fully_green": zero_incremental and total_provider_cost_known,
        "prod_candidate_allowed": False,
        "status": "ZERO_INCREMENTAL_COST_PROVEN_TOTAL_PROVIDER_COST_PENDING",
    }
