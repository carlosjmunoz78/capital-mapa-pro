from __future__ import annotations

# Evidence-only cost attribution. Shared subscriptions are never divided across
# engines or families without provider-level usage evidence.

PROVIDER_COST_EVIDENCE = {
    "supabase": {"currency": "USD", "monthly_amount": 25.00, "status": "MEASURED"},
    "make": {"currency": "USD", "monthly_amount": 10.59, "status": "MEASURED"},
    "canva": {"currency": "EUR", "monthly_amount": 16.00, "status": "MEASURED"},
    "hostinger_business_email": {"currency": "EUR", "monthly_amount": 14.50, "status": "MEASURED"},
    "google_cloud": {"currency": None, "monthly_amount": None, "status": "UNRESOLVED_PROVIDER_CONSOLE_REQUIRED"},
    "notion": {"currency": None, "monthly_amount": None, "status": "UNRESOLVED_PROVIDER_BILLING_PAGE_REQUIRED"},
}

FAMILY_PROVIDER_RELATIONS = {
    "app_crm": ("supabase",),
    "document_intelligence": ("supabase", "google_cloud"),
    "lead_ingest": ("supabase", "make"),
    "daily_reporting": ("supabase", "make"),
    "seo": ("make", "notion"),
    "social": ("make", "canva", "notion"),
    "engine_factory": (),
}


def assess_family(name: str) -> dict:
    providers = FAMILY_PROVIDER_RELATIONS[name]
    unresolved = tuple(p for p in providers if PROVIDER_COST_EVIDENCE[p]["monthly_amount"] is None)
    measured = tuple(p for p in providers if PROVIDER_COST_EVIDENCE[p]["monthly_amount"] is not None)
    return {
        "family": name,
        "providers": providers,
        "measured_providers": measured,
        "unresolved_providers": unresolved,
        "family_monthly_cost": None,
        "allocation_method": "NO_ARBITRARY_SHARED_SUBSCRIPTION_SPLIT",
        "family_cost_green": False,
    }


def assess() -> dict:
    families = {name: assess_family(name) for name in FAMILY_PROVIDER_RELATIONS}
    return {
        "provider_count": len(PROVIDER_COST_EVIDENCE),
        "family_count": len(families),
        "arbitrary_allocation_performed": False,
        "estimated_amounts_used": False,
        "all_provider_amounts_known": all(v["monthly_amount"] is not None for v in PROVIDER_COST_EVIDENCE.values()),
        "all_family_costs_attributed": False,
        "finops_green": False,
        "status": "PROVIDER_EVIDENCE_MAPPED_FAMILY_ALLOCATION_PENDING_USAGE_EVIDENCE",
    }
