from __future__ import annotations


def assess() -> dict:
    return {
        "notion_workspace_connected": True,
        "notion_cost_matrix_record_found": True,
        "notion_reference_price_usd_per_member_month": 20.0,
        "notion_reference_price_is_actual_invoice": False,
        "notion_record_explicitly_requires_real_invoice_eur": True,
        "notion_exact_monthly_amount_proven": False,
        "gcp_billing_account_notice_found": True,
        "gcp_billing_account_id": "018302-B98A9D-1DA981",
        "gcp_pending_charge_notice_found": True,
        "gcp_exact_amount_proven": False,
        "estimated_amounts_used": False,
        "finops_green": False,
        "status": "AUTHORITATIVE_CONNECTED_SOURCES_EXHAUSTED_AMOUNT_STILL_UNPROVEN",
    }
