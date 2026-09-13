from __future__ import annotations

# Evidence-only revalidation of externally authoritative billing sources.
# No payment, subscription, plan, billing setting, or provider mutation is authorized.

PROVIDERS = {
    "google_cloud": {
        "billing_email_search_revalidated": True,
        "paid_account_observed": True,
        "past_due_or_payment_issue_notice_observed": True,
        "project_suspension_warning_observed": True,
        "exact_amount_found_in_available_email_evidence": False,
        "invoice_attachment_observed": False,
        "provider_console_required_for_exact_amount": True,
    },
    "notion": {
        "billing_email_search_revalidated": True,
        "payment_failure_notices_observed": True,
        "repeated_attempt_notices_observed": True,
        "exact_amount_found_in_available_email_evidence": False,
        "invoice_attachment_observed": False,
        "provider_billing_page_required_for_exact_amount": True,
    },
}


def assess() -> dict:
    unresolved = tuple(
        name for name, row in PROVIDERS.items()
        if not row["exact_amount_found_in_available_email_evidence"]
    )
    return {
        "provider_count": len(PROVIDERS),
        "revalidated_provider_count": sum(1 for row in PROVIDERS.values() if row["billing_email_search_revalidated"]),
        "unresolved_provider_count": len(unresolved),
        "unresolved_providers": unresolved,
        "estimated_amounts_used": False,
        "billing_mutation_allowed": False,
        "finops_green": False,
        "status": "EXTERNAL_BILLING_EVIDENCE_REVALIDATED_AMOUNTS_STILL_UNRESOLVED",
    }
