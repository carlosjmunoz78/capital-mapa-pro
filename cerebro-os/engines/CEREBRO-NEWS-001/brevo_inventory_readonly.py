"""NEWS-001 · Brevo Free private inventory, read-only and no PII in reports.

This is a LAB command-line probe. It does not mutate Brevo, Contacts,
Supabase, WordPress, campaigns, or schedules. Requires a privately injected
API key. Never add it to repository, arguments, output, or logs.
"""
from __future__ import annotations
import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Callable

ROOT="https://api.brevo.com/v3"
PATH_ALLOW=(
    re.compile(r"^/account$"),
    re.compile(r"^/senders$"),
    re.compile(r"^/contacts/lists\?limit=(?:[1-9]|[1-4]\d|50)&offset=\d+$"),
    re.compile(r"^/contacts/lists/\d+/contacts\?limit=(?:[1-9]|[1-4]\d|50)&offset=\d+$"),
)
MAX_PAGES=30
PAGE_SIZE=50

class InventoryBlocked(Exception):
    pass

def _allowed(path: str) -> bool:
    return isinstance(path,str) and len(path)<180 and any(p.fullmatch(path) for p in PATH_ALLOW)

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def make_reader(api_key: str) -> Callable[[str], dict]:
    if not isinstance(api_key,str) or not api_key or len(api_key)>512:
        raise InventoryBlocked("BREVO_SECRET_NOT_CONNECTED")
    opener=urllib.request.build_opener(_NoRedirect)
    def get(path: str) -> dict:
        if not _allowed(path):
            raise InventoryBlocked("ENDPOINT_NOT_ALLOWLISTED")
        req=urllib.request.Request(
            ROOT+path, headers={"api-key":api_key,"accept":"application/json"},
            method="GET")
        try:
            with opener.open(req,timeout=10) as resp:
                if resp.status!=200:
                    raise InventoryBlocked("UNEXPECTED_HTTP_STATUS")
                raw=resp.read(1_000_001)
                if len(raw)>1_000_000:
                    raise InventoryBlocked("API_RESPONSE_TOO_LARGE")
                d=json.loads(raw)
                if not isinstance(d,dict):
                    raise InventoryBlocked("API_JSON_OBJECT_EXPECTED")
                return d
        except urllib.error.HTTPError as exc:
            raise InventoryBlocked("BREVO_HTTP_"+str(exc.code)) from None
        except urllib.error.URLError:
            raise InventoryBlocked("BREVO_NETWORK_UNAVAILABLE") from None
        except (ValueError,UnicodeError):
            raise InventoryBlocked("BREVO_BAD_JSON") from None
    return get

def _page(get:Callable[[str],dict], path:str, key:str) -> list:
    results=[]
    offset=0
    for _ in range(MAX_PAGES):
        resp=get(path.format(limit=PAGE_SIZE,offset=offset))
        items=resp.get(key)
        if not isinstance(items,list):
            raise InventoryBlocked("RESPONSE_"+key.upper()+"_MISSING")
        if any(not isinstance(x,dict) for x in items):
            raise InventoryBlocked("RESPONSE_ITEMS_INVALID")
        results.extend(items)
        if len(items)<PAGE_SIZE:
            return results
        offset+=PAGE_SIZE
    raise InventoryBlocked("PAGINATION_LIMIT_EXCEEDED")

def inspect(get:Callable[[str],dict]) -> dict:
    """Return only aggregate metadata, list names, and counts, no emails."""
    account=get("/account")
    plans=account.get("plan",[])
    if not isinstance(plans,list):plans=[]
    labels=sorted(set(x.get("type") for x in plans if isinstance(x,dict) and isinstance(x.get("type"),str)))
    senders=get("/senders").get("senders",[])
    if not isinstance(senders,list):raise InventoryBlocked("SENDERS_NOT_LIST")
    lists=_page(get,"/contacts/lists?limit={limit}&offset={offset}","lists")
    seen=set()
    ag=[]
    others=0
    for row in lists:
        lid=row.get("id")
        name=row.get("name")
        if not isinstance(lid,int) or lid<1 or lid in seen or not isinstance(name,str):
            raise InventoryBlocked("LIST_ID_OR_NAME_INVALID")
        seen.add(lid)
        if not re.search("inmobiliari",name,re.I):
            others+=1
            continue
        # The full contact list may contain email addresses; keep only aggregate
        # counts and flags in memory, never print, persist, or return raw rows.
        members=_page(get,
            "/contacts/lists/"+str(lid)+"/contacts?limit={limit}&offset={offset}","contacts")
        if len(members)>MAX_PAGES*PAGE_SIZE:
            raise InventoryBlocked("TOO_MANY_CONTACTS")
        active=0;blocked=0;unknown=0
        for c in members:
            b=c.get("emailBlacklisted")
            if b is True: blocked+=1
            elif b is False: active+=1
            else: unknown+=1
        preprod=bool(re.search("preprod|prueba|test|lab",name,re.I))
        ag.append({
            "list_id":lid,
            "name":name[:100],
            "contacts_total":len(members),
            "not_email_blacklisted":active,
            "email_blacklisted":blocked,
            "blacklist_status_unknown":unknown,
            "environment":"PREPROD_OR_TEST_HOLD" if preprod else "PROD_NOT_YET_CERTIFIED",
            "consent_evidence_verified":False,
            "eligible_for_campaign":0,
        })
    return {
        "state":"INVENTORY_READONLY_NO_SEND",
        "plans_reported":labels,
        "account_quota_verified":False,
        "senders_total":len(senders),
        "senders_with_explicit_active_true":sum(1 for x in senders if isinstance(x,dict) and x.get("active") is True),
        "lists_total":len(lists),
        "lists_without_inmobiliaria_term":others,
        "agency_lists":ag,
        "historical_particulares_imported":False,
        "send_authorized":False,
        "contact_mutation_authorized":False,
        "sensitive_contact_data_recorded":False,
    }

def main() -> int:
    if os.environ.get("NEWS001_BREVO_READONLY_ENABLED") != "true":
        print(json.dumps({"state":"BLOCKED_READONLY_NOT_ENABLED","send_authorized":False}))
        return 2
    secret=os.environ.get("BREVO_API_KEY","")
    if not secret:
        print(json.dumps({"state":"BLOCKED_BREVO_SECRET_MISSING","send_authorized":False}))
        return 2
    try:
        data=inspect(make_reader(secret))
    except InventoryBlocked as exc:
        print(json.dumps({"state":str(exc),"send_authorized":False}))
        return 2
    except Exception:
        print(json.dumps({"state":"READONLY_UNEXPECTED_FAILURE","send_authorized":False}))
        return 2
    print(json.dumps(data,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
