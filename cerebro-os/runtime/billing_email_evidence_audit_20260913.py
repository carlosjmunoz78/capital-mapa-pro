from __future__ import annotations

# Read-only Gmail billing evidence audit captured 2026-09-13.
# No payment, subscription, plan or billing mutation is authorized here.

PROVIDERS = {
    "google_cloud": {
        "billing_account": "018302-B98A9D-1DA981",
        "paid_account_upgrade_observed": True,
        "past_due_or_invalid_payment_notice_observed": True,
        "project_suspension_warning_observed": True,
        "exact_amount_present_in_available_billing_emails": False,
        "invoice_attachment_observed": False,
        "over_free_tier_proven": False,
        "status": "AMOUNT_UNRESOLVED_PROVIDER_CONSOLE_REQUIRED",
    },
    "notion": {
        "payment_failure_notices_observed": True,
        "repeated_attempt_notices_observed": True,
        "exact_amount_present_in_available_billing_emails": False,
        "invoice_attachment_observed": False,
        "status": "AMOUNT_UNRESOLVED_PROVIDER_BILLING_PAGE_REQUIRED",
    },
}


def assess() -> dict:
    unresolved = tuple(k for k, v in PROVIDERS.items() if not v["exact_amount_present_in_available_billing_emails"])
    return {
        "provider_count": len(PROVIDERS),
        "unresolved_provider_count": len(unresolved),
        "unresolved_providers": unresolved,
        "google_cloud_over_free_tier_proven": PROVIDERS["google_cloud"]["over_free_tier_proven"],
        "exact_total_due_known": False,
        "estimated_amounts_used": False,
        "billing_mutation_allowed": False,
        "finops_green": False,
        "status": "EMAIL_EVIDENCE_EXHAUSTED_EXACT_PROVIDER_BALANCES_STILL_EXTERNAL",
    }
