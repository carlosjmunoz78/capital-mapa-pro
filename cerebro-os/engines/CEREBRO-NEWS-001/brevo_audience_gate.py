"""NEWS-001 · Brevo audience gate, pure LAB reference implementation.

Never treats membership or existence in Brevo as proof of consent.
Never performs IO, imports, sends, or subscribes contacts.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re
import unicodedata

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
AUDIENCES = {"b2b": "INMOBILIARIAS_COLABORADORAS", "b2c": "PARTICULARES_NUEVOS"}
SALINAS_FIELDS = ("agency_name", "company_name", "organization", "business_name", "contact_name", "name")

def _salinas_match(contact: dict) -> bool:
    for field in SALINAS_FIELDS:
        v = contact.get(field)
        if isinstance(v, str):
            normalized = "".join(ch for ch in unicodedata.normalize("NFD", v.casefold()) if unicodedata.category(ch) != "Mn")
            if re.search(r"\bsalinas\b", normalized):
                return True
    email = contact.get("email", "")
    if isinstance(email, str) and re.search(r"(?<![a-z])salinas(?![a-z])", email.casefold()):
        return True
    return False

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
        if _salinas_match(contact):
            return hold("USER_EXCLUDED_SALINAS")
        if contact.get("salinas_screened") is not True:
            return hold("SALINAS_EXCLUSION_NOT_VERIFIED")
        if contact.get("consent_purpose") != "b2b_newsletter" or contact.get("brevo_list_verified") is not True:
            return hold("B2B_SEGMENT_OR_PURPOSE_INVALID")
        # All existing real estate agencies are candidates except Salinas,
        # subject to validated consent and global unsubscribe/suppression flags.
        segment = AUDIENCES["b2b"]
    elif persona == "inmobiliaria" and origin in ("fenix_cerebro_leads", "social_lead_form"):
        if _salinas_match(contact):
            return hold("USER_EXCLUDED_SALINAS")
        if contact.get("salinas_screened") is not True:
            return hold("SALINAS_EXCLUSION_NOT_VERIFIED")
        if contact.get("consent_purpose") != "b2b_newsletter":
            return hold("B2B_PURPOSE_INVALID")
        activation_time = _valid_time(activation_at)
        received_time = _valid_time(contact.get("lead_received_at"))
        if activation_time is None or received_time is None or received_time < activation_time:
            return hold("B2B_NEW_LEAD_ACTIVATION_NOT_VERIFIED")
        if contact.get("lead_form_verified") is not True or contact.get("double_opt_in_confirmed") is not True:
            return hold("B2B_SOURCE_OR_DOI_NOT_CONFIRMED")
        if origin == "social_lead_form":
            platform = contact.get("social_platform")
            if (contact.get("source_channel") != "social"
                or not isinstance(platform, str)
                or not 1 <= len(platform.strip()) <= 64
                or not re.fullmatch(r"[\w\s.-]+", platform.strip(), re.UNICODE)):
                return hold("B2B_SOCIAL_SOURCE_INVALID")
        elif contact.get("source_channel") != "web":
            return hold("B2B_WEB_SOURCE_INVALID")
        segment = AUDIENCES["b2b"]
    elif persona == "particular" and origin in ("fenix_cerebro_leads", "social_lead_form"):
        live_at = _valid_time(activation_at)
        lead_at = _valid_time(contact.get("lead_received_at"))
        if live_at is None or lead_at is None or lead_at < live_at:
            return hold("PARTICULAR_LEGACY_OR_ACTIVATION_UNVERIFIED")
        if contact.get("consent_purpose") != "b2c_newsletter":
            return hold("B2C_PURPOSE_INVALID")
        if contact.get("double_opt_in_confirmed") is not True:
            return hold("DOI_NOT_CONFIRMED")
        if origin == "social_lead_form":
            platform = contact.get("social_platform")
            if (contact.get("lead_form_verified") is not True
                or contact.get("source_channel") != "social"
                or not isinstance(platform, str)
                or not 1 <= len(platform.strip()) <= 64
                or not re.fullmatch(r"[\w\s.-]+", platform.strip(), re.UNICODE)):
                return hold("SOCIAL_LEAD_FORM_NOT_VERIFIED")
        elif contact.get("source_channel", "web") not in ("web", "social"):
            return hold("SOURCE_CHANNEL_INVALID")
        segment = AUDIENCES["b2c"]
    else:
        return hold("AUDIENCE_SOURCE_NOT_ALLOWED")
    return {"state": "ELIGIBLE_FOR_PREPROD_TEST_ONLY", "segment": segment,
            "reason": "SEGMENT_AND_EVIDENCE_VERIFIED",
            "send_authorized": False, "contact_mutation_authorized": False}
