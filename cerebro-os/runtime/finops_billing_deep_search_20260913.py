from __future__ import annotations

# Read-only billing evidence revalidated 2026-09-14 from the connected mailbox.
# No provider mutation, payment, subscription, plan or billing change is authorized.
# Exact monetary amounts are intentionally not inferred from plan names or seat counts.

EVIDENCE = {
    "notion": {
        "authoritative_sender_evidence": True,
        "plan": "Plus",
        "renewing_seats": 3,
        "renewal_date_evidence": "2025-04-10",
        "recent_payment_failure_notice_evidence": True,
        "recent_payment_failure_notice_date": "2026-08-08",
        "exact_amount_found": False,
        "invoice_attachment_found": False,
        "safe_conclusion": "plan_and_seat_count_confirmed_but_exact_monthly_amount_not_present_in_email_evidence",
    },
    "google_cloud": {
        "authoritative_sender_evidence": True,
        "paid_account_upgrade_notice_evidence": True,
        "paid_account_upgrade_notice_date": "2026-08-18",
        "recent_billing_problem_notice_evidence": True,
        "recent_billing_problem_notice_date": "2026-09-12",
        "trading_lab_suspension_warning_evidence": True,
        "exact_amount_found": False,
        "invoice_attachment_found": False,
        "safe_conclusion": "paid_billing_and_payment_problem_confirmed_but_exact_amount_not_present_in_email_evidence",
    },
}


def assess() -> dict:
    unresolved = tuple(name for name, row in EVIDENCE.items() if not row["exact_amount_found"])
    return {
        "provider_count": len(EVIDENCE),
        "unresolved_provider_count": len(unresolved),
        "unresolved_providers": unresolved,
        "email_search_space_deepened": True,
        "authoritative_provider_email_evidence_revalidated_2026_09_14": True,
        "notion_plan_and_seats_known": True,
        "google_cloud_paid_billing_problem_known": True,
        "estimated_amounts_used": False,
        "provider_console_still_required": True,
        "finops_green": False,
        "status": "AUTHORITATIVE_EMAIL_EVIDENCE_RICHER_EXACT_AMOUNTS_STILL_EXTERNAL",
    }
