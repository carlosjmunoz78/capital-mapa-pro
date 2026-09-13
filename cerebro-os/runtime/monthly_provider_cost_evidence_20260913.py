from __future__ import annotations

# Evidence-only monthly provider cost snapshot. No billing mutation is authorized.
# Amounts are recorded only where a recent invoice/receipt or recurring charge
# has been directly observed. Unknown providers remain unknown rather than estimated.

MEASURED_PROVIDER_COSTS = {
    "supabase": {"currency": "USD", "monthly_amount": 25.00, "evidence": "RECENT_INVOICE"},
    "make": {"currency": "USD", "monthly_amount": 10.59, "evidence": "RECENT_RECEIPT"},
    "canva": {"currency": "EUR", "monthly_amount": 16.00, "evidence": "RECENT_MONTHLY_INVOICE"},
    "hostinger_business_email": {"currency": "EUR", "monthly_amount": 14.50, "evidence": "PLAN_PRICE_PLUS_TAX"},
}

UNRESOLVED_PROVIDER_COSTS = {
    "notion": "PAYMENT_FAILURE_CONFIRMED_AMOUNT_NOT_PRESENT_IN_AVAILABLE_BILLING_EMAILS",
    "google_cloud": "BILLING_ACCOUNT_ACTIVE_OR_PAST_DUE_EXACT_MONTHLY_AMOUNT_NOT_OBSERVED",
}


def assess_monthly_provider_cost_evidence() -> dict:
    usd_total = sum(v["monthly_amount"] for v in MEASURED_PROVIDER_COSTS.values() if v["currency"] == "USD")
    eur_total = sum(v["monthly_amount"] for v in MEASURED_PROVIDER_COSTS.values() if v["currency"] == "EUR")
    return {
        "measured_provider_count": len(MEASURED_PROVIDER_COSTS),
        "measured_usd_monthly": round(usd_total, 2),
        "measured_eur_monthly": round(eur_total, 2),
        "unresolved_provider_count": len(UNRESOLVED_PROVIDER_COSTS),
        "unresolved_providers": tuple(sorted(UNRESOLVED_PROVIDER_COSTS)),
        "all_provider_costs_measured": not UNRESOLVED_PROVIDER_COSTS,
        "currency_conversion_applied": False,
        "estimated_amounts_used": False,
        "billing_mutation_allowed": False,
        "status": "PARTIAL_REAL_BILLING_EVIDENCE_REMAINING_PROVIDERS_PENDING",
    }
