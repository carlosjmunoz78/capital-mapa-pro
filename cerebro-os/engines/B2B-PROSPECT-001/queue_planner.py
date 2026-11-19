"""B2B-PROSPECT-001. Deterministic NO-NETWORK lab planner; NEVER sends e-mail.
The integer priority governs admission to one continuous queue, NOT phase gates.
An official municipality inventory is a separate future, verified input.
"""
from __future__ import annotations
from hashlib import sha256
import unicodedata

ROUTE = (
    ("cordoba", "towns"), ("jaen", "towns"), ("jaen", "capital"),
    ("sevilla", "towns"), ("sevilla", "capital"), ("malaga", "towns"),
    ("malaga", "capital"), ("granada", "towns"), ("granada", "capital"),
    ("cadiz", "towns"), ("cadiz", "capital"), ("almeria", "towns"),
    ("almeria", "capital"), ("huelva", "towns"), ("huelva", "capital"),
)
MAX_ACCOUNT_DAILY_EMAILS = 300

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(x for x in value if not unicodedata.combining(x)).casefold().strip()

def priority(province, *, is_capital):
    key = (normalize(province), "capital" if is_capital else "towns")
    try:
        return ROUTE.index(key) + 1
    except ValueError:
        return None  # Cordoba capital is intentionally unlisted by the owner.

def queue_key(row):
    identity = "|".join(normalize(row.get(x)) for x in ("company_id", "business_name", "municipality", "province", "email"))
    return sha256(identity.encode()).hexdigest()

def prepare(rows):
    """Return a deduped order preview only; never an outreach authorization."""
    if not isinstance(rows, (list, tuple)):
        raise TypeError("rows must be a list/tuple")
    prepared = []
    seen = set()
    held = []
    for row in rows:
        if not isinstance(row, dict) or row.get("company_id") != "fenix":
            held.append({"reason": "INVALID_COMPANY"}); continue
        p = priority(row.get("province"), is_capital=row.get("is_capital") is True)
        name = normalize(row.get("business_name"))
        if p is None or not name or not normalize(row.get("municipality")):
            held.append({"reason": "UNKNOWN_PRIORITY_OR_IDENTITY"}); continue
        token = queue_key(row)
        if token in seen:
            held.append({"reason": "DUPLICATE"}); continue
        seen.add(token)
        if "salinas" in normalize(name + " " + str(row.get("email", ""))) or row.get("suppressed") is True:
            held.append({"reason": "SUPPRESSED_OR_EXCLUDED"}); continue
        prepared.append({
            "priority": p, "company_id": "fenix", "engine_id": "B2B-PROSPECT-001",
            "municipality": row["municipality"], "business_name": row["business_name"],
            "idempotency_key": token, "status": "DISCOVERED_ONLY", "send_authorized": False,
        })
    prepared.sort(key=lambda x: (x["priority"], normalize(x["municipality"]), normalize(x["business_name"]), x["idempotency_key"]))
    return {"state": "LAB_PLANNED_NO_SEND", "queue": prepared, "held": held,
            "queue_size": len(prepared), "emails_sent": 0, "brevo_mutations": 0}

def preview_daily(ordered_queue, *, verified_daily_limit, remaining_quota, reserved_for_existing):
    """No send. The account-wide free cap and reserved ongoing newsletters MUST be respected."""
    ints = (verified_daily_limit, remaining_quota, reserved_for_existing)
    if any(type(x) is not int or x < 0 for x in ints) or remaining_quota > verified_daily_limit:
        return {"state": "HOLD_INVALID_QUOTA", "proposed": [], "send_authorized": False}
    available = max(0, min(MAX_ACCOUNT_DAILY_EMAILS, verified_daily_limit, remaining_quota) - reserved_for_existing)
    items = list(ordered_queue)
    return {"state": "LAB_CAPACITY_PREVIEW_NO_SEND", "available_email_slots": available,
            "proposed": [dict(x, send_authorized=False) for x in items[:available]],
            "deferred_count": max(0, len(items) - available), "send_authorized": False,
            "emails_sent": 0, "brevo_mutations": 0}
