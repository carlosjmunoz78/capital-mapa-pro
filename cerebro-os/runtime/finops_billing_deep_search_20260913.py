from __future__ import annotations

# Read-only deep billing search evidence captured 2026-09-13.
# No provider mutation, payment, subscription, plan or billing change is authorized.

EVIDENCE = {
    "notion": {
        "invoice_or_receipt_search_after_2026_01_01": "NO_MATCHES",
        "money_term_search_after_2026_01_01": "PAYMENT_FAILURE_NOTICES_ONLY",
        "exact_amount_found": False,
        "invoice_attachment_found": False,
    },
    "google_cloud": {
        "invoice_or_receipt_search_after_2026_01_01": "SUSPENSION_OR_BILLING_WARNINGS_ONLY",
        "billing_account_amount_search": "NO_MATCHES",
        "exact_amount_found": False,
        "invoice_attachment_found": False,
    },
}


def assess() -> dict:
    unresolved = tuple(name for name, row in EVIDENCE.items() if not row["exact_amount_found"])
    return {
        "provider_count": len(EVIDENCE),
        "unresolved_provider_count": len(unresolved),
        "unresolved_providers": unresolved,
        "email_search_space_deepened": True,
        "estimated_amounts_used": False,
        "provider_console_still_required": True,
        "finops_green": False,
        "status": "EMAIL_SEARCH_EXHAUSTED_MORE_DEEPLY_EXACT_AMOUNTS_STILL_EXTERNAL",
    }
