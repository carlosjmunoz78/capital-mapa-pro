"""CP82 - fail-closed proof of a private JARVIS -> FACT-001 READ operation.

This module does not grant IAM privileges, call Cloudflare, create signatures for
services, or deploy a Gateway. Services must sign and persist genuine receipts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Callable, Mapping

SCHEMA="cerebro.private-read.v1"
TARGET_ENGINE="FACT-001"
CAPABILITY="FACT.INVENTORY.READ"  # proposed CP82 contract, NOT a deployed RPC
REQUIRED_SCOPE=("request_id","company_id","engine_id","environment",
                "version","capability","read_only","external_mutation_allowed",
                "cost_ceiling_eur","emitted_at_epoch")
FORBIDDEN_FIELDS=frozenset(("token","password","secret","api_key","private_key",
                            "credential_value","access_jwt","cookie"))

def _canonical(value:Mapping)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def _assert_no_secrets(value)->None:
    if isinstance(value,dict):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise ValueError("raw credentials forbidden in remote receipt")
            _assert_no_secrets(child)
    elif isinstance(value,list):
        for child in value:
            _assert_no_secrets(child)

def assess_live_observation(observation:dict)->dict:
    """Classify independently verified source observations, never infer E2E."""
    if not isinstance(observation,dict):
        raise ValueError("observation must be an object")
    access=observation.get("access") or {}
    fact=observation.get("fact") or {}
    gateway=observation.get("gateway") or {}
    source=bool(access.get("owner_match") is True and access.get("allowed") is True)
    read=bool(fact.get("company_id") and
              fact.get("engine_id")==TARGET_ENGINE and
              fact.get("environment")=="LAB" and
              fact.get("operation")=="providers.five.inventory.read" and
              type(fact.get("completed_jobs")) is int and fact["completed_jobs"]>0)
    private_binding=bool(gateway.get("jarvis_fact_binding_verified") is True)
    signed_pair=bool(gateway.get("correlated_signed_receipt_verified") is True)
    enterprise_iam=bool(gateway.get("enterprise_iam_verified") is True)
    # These claims alone are insufficient: without an independent stored
    # signed receipt reader, a real E2E result must never become GREEN.
    missing=[]
    if not source: missing.append("ACCESS_OWNER_IDENTITY_UNVERIFIED")
    if not read: missing.append("FACT_REMOTE_READ_UNVERIFIED")
    if not private_binding: missing.append("JARVIS_FACT_SERVICE_BINDING_MISSING")
    if not enterprise_iam: missing.append("ENTERPRISE_IAM_UNVERIFIED")
    if not signed_pair: missing.append("CORRELATED_SIGNED_RECEIPT_MISSING")
    missing.append("LIVE_E2E_RECEIPT_RETRIEVAL_REQUIRED")
    return {"status":"BLOCKED","environment":"LAB","engine_id":TARGET_ENGINE,
            "source_owner_access_verified":source,"fact_d1_inventory_verified":read,
            "jarvis_fact_e2e_verified":False,"promotion_allowed":False,
            "missing":tuple(missing),"external_mutation_allowed":False}

def _require_scope(body:Mapping,*,company_id:str,request_id:str,now_epoch:int,max_age_s:int)->None:
    if not isinstance(body,dict):
        raise ValueError("receipt must be an object")
    _assert_no_secrets(body)
    if any(k not in body for k in REQUIRED_SCOPE):
        raise ValueError("remote receipt scope missing")
    if body.get("request_id")!=request_id or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,128}",request_id):
        raise ValueError("remote receipt correlation mismatch")
    if not isinstance(company_id,str) or not company_id.strip() or body.get("company_id")!=company_id:
        raise ValueError("remote receipt company mismatch")
    if body.get("engine_id")!=TARGET_ENGINE or body.get("environment")!="LAB":
        raise ValueError("remote receipt engine/environment denied")
    if body.get("capability")!=CAPABILITY or not re.fullmatch(r"\d+\.\d+\.\d+",str(body.get("version",""))):
        raise ValueError("remote receipt capability/version denied")
    if body.get("read_only") is not True or body.get("external_mutation_allowed") is not False:
        raise ValueError("remote receipt mutation forbidden")
    if type(body.get("cost_ceiling_eur")) not in (int,float) or body["cost_ceiling_eur"]!=0:
        raise ValueError("remote receipt cost ceiling denied")
    event_time=body.get("emitted_at_epoch")
    if type(event_time) is not int or event_time>now_epoch+30 or now_epoch-event_time>max_age_s:
        raise ValueError("remote receipt freshness denied")

def verify_private_read_pair(*,jarvis:dict,fact:dict,
                             jarvis_signature:str,fact_signature:str,
                             jarvis_key:bytes,fact_key:bytes,
                             company_id:str,request_id:str,now_epoch:int,
                             persisted_fact_reader:Callable[[str],dict|None],
                             max_age_s:int=300)->dict:
    """Accept only two separate service MACs plus matching durable FACT receipt.

    The caller must supply real service keys from an external Vault, never from
    a request. Storage reader must fetch a previously persisted remote receipt.
    """
    if not callable(persisted_fact_reader):
        raise ValueError("independent persistent reader required")
    if any(type(k) is not bytes or len(k)<32 for k in (jarvis_key,fact_key)) or jarvis_key==fact_key:
        raise ValueError("distinct service keys required")
    if type(now_epoch) is not int or now_epoch<0 or type(max_age_s) is not int or max_age_s<1:
        raise ValueError("valid verification time required")
    for item in (jarvis,fact):
        _require_scope(item,company_id=company_id,request_id=request_id,
                       now_epoch=now_epoch,max_age_s=max_age_s)
        if item.get("schema")!=SCHEMA:
            raise ValueError("remote receipt schema denied")
    if jarvis.get("origin")!="JARVIS" or jarvis.get("target")!=TARGET_ENGINE or        jarvis.get("owner_access_verified") is not True or        jarvis.get("iam_policy")!="ALLOW_READ_ONLY" or        not str(jarvis.get("policy_receipt_ref","")).strip():
        raise ValueError("JARVIS identity/policy proof missing")
    if fact.get("origin")!=TARGET_ENGINE or fact.get("target")!="JARVIS" or        fact.get("status")!="COMPLETED" or        not re.fullmatch(r"[0-9a-f]{64}",str(fact.get("result_sha256",""))):
        raise ValueError("FACT read receipt invalid")
    if jarvis.get("version")!=fact.get("version"):
        raise ValueError("remote receipt version mismatch")
    if type(jarvis_signature) is not str or type(fact_signature) is not str or        not re.fullmatch(r"[0-9a-f]{64}",jarvis_signature) or        not re.fullmatch(r"[0-9a-f]{64}",fact_signature):
        raise ValueError("receipt MAC format invalid")
    expected_j=hmac.new(jarvis_key,_canonical(jarvis),hashlib.sha256).hexdigest()
    expected_f=hmac.new(fact_key,_canonical(fact),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(jarvis_signature,expected_j):
        raise PermissionError("JARVIS receipt MAC invalid")
    if not hmac.compare_digest(fact_signature,expected_f):
        raise PermissionError("FACT receipt MAC invalid")
    stored=persisted_fact_reader(request_id)
    if not isinstance(stored,dict) or stored!=fact:
        raise PermissionError("independent persisted FACT receipt mismatch")
    return {"status":"VERIFIED_PAIR","engine_id":TARGET_ENGINE,
            "company_id":company_id,"environment":"LAB","request_id":request_id,
            "capability":CAPABILITY,"read_only":True,
            "external_mutation_allowed":False,"production_activation_allowed":False,
            "cost_ceiling_eur":0,"promotion_allowed":False,
            "fact_receipt_sha256":hashlib.sha256(_canonical(fact)).hexdigest(),
            "note":"Receipt pairing only; production promotion requires independent gates"}


def verify_authorized_private_read(*, trusted_grant_reader, expected_principal: str,
                                   expected_issuer: str, canonical_company_id: str,
                                   **pair):
    """CP131: verify a receipt pair against an independent, trusted IAM grant.

    The reader and expected identities are server-side ports, not user inputs.
    It must return a verified, live, revocation-checked grant projection from IAM.
    This function neither issues a grant nor certifies its deployment.
    """
    if not callable(trusted_grant_reader):
        raise PermissionError("CP131_TRUSTED_IAM_READER_REQUIRED")
    if any(not isinstance(x, str) or not x.strip() for x in
           (expected_principal, expected_issuer, canonical_company_id)):
        raise ValueError("CP131_TRUSTED_CONTEXT_REQUIRED")
    if expected_principal == expected_issuer or pair.get("company_id") != canonical_company_id:
        raise PermissionError("CP131_IDENTITY_SCOPE_DENIED")
    age = pair.get("max_age_s", 300)
    if type(age) is not int or not 1 <= age <= 300:
        raise ValueError("CP131_RECEIPT_AGE_DENIED")
    verified = verify_private_read_pair(**pair)
    jarvis, fact = pair["jarvis"], pair["fact"]
    ref = jarvis["policy_receipt_ref"]
    if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{8,200}", ref):
        raise PermissionError("CP131_GRANT_REFERENCE_DENIED")
    if any(x.get("principal_id") != expected_principal or x.get("policy_receipt_ref") != ref
           for x in (jarvis, fact)):
        raise PermissionError("CP131_RECEIPT_GRANT_BINDING_DENIED")
    grant = trusted_grant_reader(ref)
    if not isinstance(grant, dict):
        raise PermissionError("CP131_GRANT_NOT_FOUND")
    _assert_no_secrets(grant)
    required = {"policy_receipt_ref": ref, "issuer_id": expected_issuer,
                "principal_id": expected_principal, "company_id": canonical_company_id,
                "request_id": pair["request_id"], "engine_id": TARGET_ENGINE,
                "environment": "LAB", "version": jarvis["version"], "capability": CAPABILITY,
                "decision": "ALLOW_READ_ONLY"}
    if any(grant.get(k) != v for k, v in required.items()):
        raise PermissionError("CP131_GRANT_SCOPE_DENIED")
    if (grant.get("verified") is not True or grant.get("active") is not True or
            grant.get("revoked") is not False or grant.get("read_only") is not True or
            grant.get("external_mutation_allowed") is not False or
            type(grant.get("cost_ceiling_eur")) not in (int, float) or grant["cost_ceiling_eur"] != 0):
        raise PermissionError("CP131_GRANT_POLICY_DENIED")
    start, end, now = grant.get("issued_at_epoch"), grant.get("expires_at_epoch"), pair["now_epoch"]
    if (type(start) is not int or type(end) is not int or not 0 <= start <= now < end or
            not 0 < end - start <= 900 or
            any(not start <= x["emitted_at_epoch"] < end for x in (jarvis, fact))):
        raise PermissionError("CP131_GRANT_LIFETIME_DENIED")
    return {**verified, "status": "VERIFIED_AUTHORIZED_PAIR", "iam_grant_verified": True,
            "promotion_allowed": False,
            "note": "Verified pair under supplied trusted IAM port; physical deployment remains a separate gate"}
