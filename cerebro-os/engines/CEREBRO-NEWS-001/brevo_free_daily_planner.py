"""NEWS001 · Brevo Free send planner (pure LAB, NEVER performs network I/O).

The verified account quota must be passed explicitly. This file never sends or
schedules e-mails; it produces a deterministic, deduplicated dispatch proposal.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256

MAX_FREE_DAY = 300
ORDER = ("welcome_b2c", "welcome_b2b", "newsletter_b2b", "newsletter_b2c")

def _valid_job(j):
    if not isinstance(j, dict): return False
    if j.get("company_id") != "fenix" or j.get("audience") not in ("b2c","b2b"):return False
    if j.get("kind") not in ORDER:return False
    if j["kind"].endswith("b2c") != (j["audience"]=="b2c"):return False
    if j.get("cohort_gate") != "ELIGIBLE_FOR_PREPROD_TEST_ONLY":return False
    if j.get("unsubscribed") is not False or j.get("suppressed") is not False:return False
    if j.get("contact_evidence_verified") is not True:return False
    if j.get("editorial_approved") is not True or j.get("visual_qa_pass") is not True:return False
    if j.get("newsletter_id") is None or j.get("contact_ref") is None:return False
    return all(isinstance(j.get(k),str) and 1 <= len(j[k]) <= 128
               for k in ("newsletter_id","contact_ref"))

def _key(j):
    return sha256(("fenix|"+j["newsletter_id"]+"|"+j["contact_ref"]+
                   "|"+j["kind"]).encode()).hexdigest()

def simulate_day(jobs, *, account_quota_verified=False,
                 provider_daily_limit=None, provider_remaining=None,
                 previously_dispatched=None):
    """Only PLAN. All returned entries keep send_authorized=False."""
    if account_quota_verified is not True or type(provider_daily_limit) is not int \
       or type(provider_remaining) is not int:
        return {"state":"BLOCKED_ACCOUNT_QUOTA_UNVERIFIED","planned":[],"deferred":[]}
    if provider_daily_limit<0 or provider_remaining<0 or provider_remaining>provider_daily_limit:
        return {"state":"BLOCKED_INVALID_QUOTA","planned":[],"deferred":[]}
    cap=min(MAX_FREE_DAY,provider_daily_limit,provider_remaining)
    if not isinstance(jobs,(list,tuple)) or len(jobs)>10000:
        return {"state":"BLOCKED_INVALID_BATCH","planned":[],"deferred":[]}
    done=set(previously_dispatched or ())
    if any(not isinstance(x,str) for x in done):
        return {"state":"BLOCKED_INVALID_DEDUPE","planned":[],"deferred":[]}
    buckets=defaultdict(list)
    seen=set(done)
    held,duplicates=0,0
    for j in jobs:
        if not _valid_job(j):
            held+=1;continue
        token=_key(j)
        if token in seen:
            duplicates+=1;continue
        seen.add(token)
        buckets[j["kind"]].append((token,j))
    for k in ORDER:buckets[k].sort(key=lambda it:(it[1]["newsletter_id"],it[0]))
    # Send welcome first, then round-robin campaigns so one audience cannot starve the other.
    scheduled=[]
    for kind in ("welcome_b2c","welcome_b2b"):
        while buckets[kind] and len(scheduled)<cap: scheduled.append(buckets[kind].pop(0))
    for kind in ("newsletter_b2b","newsletter_b2c"):
        pass
    while len(scheduled)<cap and (buckets["newsletter_b2b"] or buckets["newsletter_b2c"]):
        for k in ("newsletter_b2b","newsletter_b2c"):
            if len(scheduled)>=cap:break
            if buckets[k]:scheduled.append(buckets[k].pop(0))
    deferred=sum(map(len,buckets.values()))
    return {"state":"LAB_PROPOSAL_ONLY","account_daily_cap":cap,
            "planned":[{"idempotency_key":t,"kind":j["kind"],"audience":j["audience"],
                        "send_authorized":False} for t,j in scheduled],
            "deferred_count":deferred,"held_count":held,"deduplicated_count":duplicates,
            "sent_count":0,"company_id":"fenix","brevo_mutated":False}
