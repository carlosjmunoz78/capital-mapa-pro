"""NEWS001 welcome and subscription plan; NO sends, no APIs, no contact writes."""
from __future__ import annotations
from brevo_audience_gate import audience_eligibility
import re

TARGETS = {
    "INMOBILIARIAS_COLABORADORAS": {"list_id": 18, "template_family": "b2b"},
    "PARTICULARES_NUEVOS": {"list_id": 17, "template_family": "b2c"},
}

def route_verified_lead(contact: dict, *, activation_at: str | None, event_id: str | None) -> dict:
    """Deterministic plan from trusted source event; no delivery authorization.

    All required user consent and unsubscribes must already be independently verified
    by an authenticated ingester, not simply claimed in a browser JSON payload.
    """
    common = {"company_id": "fenix", "engine_id": "CEREBRO-NEWS-001",
              "environment": "LAB", "version": "0.4.0", "send_enabled": False,
              "brevo_contacts_mutation_enabled": False}
    def hold(code):
        return {**common, "state": "HOLD", "reason": code,
                "list_id": None, "template_family": None,
                "actions": [], "eligible_for_live_send": False}
    if not isinstance(contact, dict):
        return hold("INVALID_CONTACT")
    if not activation_at:
        return hold("NO_ACTIVATION_TIMESTAMP")
    if not isinstance(event_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,128}",event_id):
        return hold("INVALID_EVENT_ID")
    if contact.get("trusted_ingest_verified") is not True:
        return hold("INGEST_PROVENANCE_NOT_VERIFIED")
    result = audience_eligibility(contact, activation_at=activation_at)
    if result["state"] != "ELIGIBLE_FOR_PREPROD_TEST_ONLY":
        return hold(result["reason"])
    target = TARGETS.get(result["segment"])
    if not target:
        return hold("NO_SEGMENT_MAP")
    return {**common, "state": "PREPROD_DRY_RUN_ELIGIBLE",
            "reason": "SOURCE_SEGMENT_AND_CONSENT_VALIDATED",
            "event_id": event_id, "list_id": target["list_id"],
            "template_family": target["template_family"],
            "actions": ["plan_verified_subscribe", "plan_doi_completed_welcome",
                        "plan_following_weekly_issue"],
            "eligible_for_live_send": False}
