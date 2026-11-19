"""B2B-PROSPECT-001: deterministic LAB planner. NO NETWORK, NO SEND."""
from __future__ import annotations
import csv
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
import unicodedata

ROUTE = (
    ("cordoba", "towns"), ("jaen", "towns"), ("jaen", "capital"),
    ("sevilla", "towns"), ("sevilla", "capital"), ("malaga", "towns"),
    ("malaga", "capital"), ("granada", "towns"), ("granada", "capital"),
    ("cadiz", "towns"), ("cadiz", "capital"), ("almeria", "towns"),
    ("almeria", "capital"), ("huelva", "towns"), ("huelva", "capital"),
)
MAX_ACCOUNT_DAILY_EMAILS = 300
CATALOG_PATH = Path(__file__).resolve().parent / "data" / "municipalities_ine_2026_andalucia.csv"
ALIASES = {"inmo hogar lucena": "lucena hogar inmobiliaria"}

def normalize(value):
    s = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(ch for ch in s if not unicodedata.combining(ch)).casefold().split())

def identity(name):
    n = normalize(name)
    return ALIASES.get(n, n)

def priority(province, *, is_capital):
    key = (normalize(province), "capital" if is_capital else "towns")
    try:
        return ROUTE.index(key) + 1
    except ValueError:
        return None

@lru_cache(maxsize=1)
def municipality_catalog():
    result, codes = {}, set()
    with CATALOG_PATH.open(newline="", encoding="utf-8") as handle:
        for item in csv.DictReader(handle):
            key = (normalize(item["province"]), normalize(item["municipality"]))
            if key in result or item["ine_code"] in codes or len(item["ine_code"]) != 5:
                raise ValueError("duplicate or malformed INE municipality")
            codes.add(item["ine_code"])
            result[key] = item
    if len(result) != 785 or sum(bool(r["queue_priority"]) for r in result.values()) != 784:
        raise ValueError("incomplete 2026 Andalusian municipality snapshot")
    return result

def municipality_route():
    rows = [r for r in municipality_catalog().values() if r["queue_priority"]]
    return sorted(rows, key=lambda r: (int(r["queue_priority"]), normalize(r["municipality"]), r["ine_code"]))

def queue_key(row):
    identifier = "|".join(normalize(x) for x in (
        row.get("company_id"), row.get("province"), row.get("municipality"),
        identity(row.get("business_name"))))
    return sha256(identifier.encode("utf-8")).hexdigest()

def _domain(url):
    try:
        u = urlsplit(str(url or ""))
        return (u.hostname or "").casefold().removeprefix("www.") if u.scheme in ("https", "http") else ""
    except ValueError:
        return ""

def _match(row, known):
    email = normalize(row.get("email"))
    agency = identity(row.get("business_name"))
    town = normalize(row.get("municipality"))
    domain = _domain(row.get("website"))
    for candidate in known:
        if not isinstance(candidate, dict):
            continue
        if email and email == normalize(candidate.get("email")):
            return True
        if domain and domain == _domain(candidate.get("website")):
            return True
        if agency and agency == identity(candidate.get("business_name")) and (
            not candidate.get("municipality") or town == normalize(candidate.get("municipality"))):
            return True
    return False

def prepare(rows, *, existing_agencies=(), brevo_contacts=(), suppressions=()):
    """Read-only data inputs. No source or email implies permission to market."""
    if not isinstance(rows, (tuple, list)):
        raise TypeError("rows must be a list or tuple")
    catalog = municipality_catalog()
    suppressed = {normalize(x) for x in suppressions}
    queue, held = [], []
    seen_keys, seen_email, seen_domains = set(), set(), set()
    for row in rows:
        if not isinstance(row, dict) or row.get("company_id") != "fenix":
            held.append({"reason": "INVALID_COMPANY"}); continue
        name = identity(row.get("business_name"))
        town = catalog.get((normalize(row.get("province")), normalize(row.get("municipality"))))
        if not name or town is None:
            held.append({"reason": "UNVERIFIED_MUNICIPALITY_OR_IDENTITY"}); continue
        is_capital = town["is_capital"] == "true"
        if "is_capital" in row and row["is_capital"] is not is_capital:
            held.append({"reason": "CAPITAL_FLAG_CONFLICT"}); continue
        p = int(town["queue_priority"] or 0)
        if not p:
            held.append({"reason": "OUT_OF_OWNER_ROUTE"}); continue
        key = queue_key(row)
        email = normalize(row.get("email"))
        domain = _domain(row.get("website"))
        if key in seen_keys or (email and email in seen_email) or (domain and domain in seen_domains):
            held.append({"reason": "DUPLICATE"}); continue
        seen_keys.add(key)
        if email: seen_email.add(email)
        if domain: seen_domains.add(domain)
        if (row.get("suppressed") is True or row.get("unsubscribed") is True or
            "salinas" in name or "salinas" in email or
            name in suppressed or email in suppressed or domain in suppressed):
            held.append({"reason": "SUPPRESSED_OR_EXCLUDED"}); continue
        if _match(row, existing_agencies):
            held.append({"reason": "PROTECTED_EXISTING_COLLABORATOR"}); continue
        if _match(row, brevo_contacts):
            held.append({"reason": "ALREADY_IN_BREVO"}); continue
        url = str(row.get("source_url") or "")
        provenance = bool(_domain(url) and row.get("source_verified_at"))
        queue.append({
            "priority": p, "company_id": "fenix", "engine_id": "B2B-PROSPECT-001",
            "environment": "LAB", "version": "0.2.0",
            "ine_code": town["ine_code"], "province": town["province"],
            "municipality": town["municipality"], "business_name": row["business_name"],
            "email": email, "website": row.get("website") or "", "source_url": url,
            "source_verified_at": row.get("source_verified_at") or "",
            "source_status": "PROVENANCE_RECORDED" if provenance else "SOURCE_REVIEW_REQUIRED",
            "legal_contact_basis": "UNVERIFIED", "contact_status": "DISCOVERED_ONLY",
            "idempotency_key": key, "send_authorized": False,
        })
    queue.sort(key=lambda x: (x["priority"], normalize(x["municipality"]),
                              normalize(x["business_name"]), x["idempotency_key"]))
    return {"state": "LAB_PLANNED_NO_SEND", "queue": queue, "held": held,
            "queue_size": len(queue), "emails_sent": 0, "brevo_mutations": 0}

def preview_daily(ordered_queue, *, verified_daily_limit, remaining_quota, reserved_for_existing):
    """Capacity is only a preview; there is deliberately no send transport."""
    args = (verified_daily_limit, remaining_quota, reserved_for_existing)
    if any(type(x) is not int or x < 0 for x in args) or remaining_quota > verified_daily_limit:
        return {"state": "HOLD_INVALID_QUOTA", "proposed": [], "send_authorized": False}
    available = max(0, min(300, verified_daily_limit, remaining_quota) - reserved_for_existing)
    items = list(ordered_queue)
    return {"state": "LAB_CAPACITY_PREVIEW_NO_SEND", "available_email_slots": available,
            "proposed": [dict(x, send_authorized=False) for x in items[:available]],
            "deferred_count": max(0, len(items) - available), "send_authorized": False,
            "emails_sent": 0, "brevo_mutations": 0}
