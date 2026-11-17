"""NEWS-001 · Brevo audience gate, pure LAB reference implementation.

Never treats membership or existence in Brevo as proof of consent.
Never performs IO, imports, sends, or subscribes contacts.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
AUDIENCES = {"b2b": "INMOBILIARIAS_COLABORADORAS", "b2c": "PARTICULARES_NUEVOS"}

def _valid_time(raw: str):
    if not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None
    except ValueError:
        return None

def audience_eligibility(contact: dict, *, activation_at: str) -> dict:
    """Routing only; green result is NOT authorization to send."""
    def hold(code):
        return {"state": "HOLD", "reason": code, "segment": None,
                "send_authorized": False, "contact_mutation_authorized": False}
    if not isinstance(contact, dict):
        return hold("BAD_CONTACT")
    if contact.get("company_id") != "fenix":
        return hold("COMPANY_SCOPE")
    email = contact.get("email", "")
    if not isinstance(email, str) or len(email) > 254 or not EMAIL_RE.fullmatch(email):
        return hold("INVALID_EMAIL")
    if contact.get("suppressed") is not False or contact.get("unsubscribed") is not False or contact.get("hard_bounced") is not False:
        return hold("SUPPRESSED_OR_UNKNOWN_STATUS")
    if contact.get("marketing_consent") is not True:  # string "true" is NOT a boolean
        return hold("MARKETING_CONSENT_NOT_VERIFIED")
    if not isinstance(contact.get("consent_evidence_id"), str) or not contact["consent_evidence_id"].strip():
        return hold("CONSENT_EVIDENCE_MISSING")
    if contact.get("consent_purpose") not in ("b2b_newsletter", "b2c_newsletter"):
        return hold("CONSENT_PURPOSE_MISSING")
    consent_at = _valid_time(contact.get("consent_at"))
    if consent_at is None:
        return hold("CONSENT_TIMESTAMP_MISSING")
    persona, origin = contact.get("persona"), contact.get("origin")
    if persona == "inmobiliaria" and origin == "brevo_existing":
        if contact.get("consent_purpose") != "b2b_newsletter" or contact.get("brevo_list_verified") is not True:
            return hold("B2B_SEGMENT_OR_PURPOSE_INVALID")
        segment = AUDIENCES["b2b"]
    elif persona == "particular" and origin == "fenix_cerebro_leads":
        live_at = _valid_time(activation_at)
        lead_at = _valid_time(contact.get("lead_received_at"))
        if live_at is None or lead_at is None or lead_at < live_at:
            return hold("PARTICULAR_LEGACY_OR_ACTIVATION_UNVERIFIED")
        if contact.get("consent_purpose") != "b2c_newsletter":
            return hold("B2C_PURPOSE_INVALID")
        if contact.get("double_opt_in_confirmed") is not True:
            return hold("DOI_NOT_CONFIRMED")
        segment = AUDIENCES["b2c"]
    else:
        return hold("AUDIENCE_SOURCE_NOT_ALLOWED")
    return {"state": "ELIGIBLE_FOR_PREPROD_TEST_ONLY", "segment": segment,
            "reason": "SEGMENT_AND_EVIDENCE_VERIFIED",
            "send_authorized": False, "contact_mutation_authorized": False}
