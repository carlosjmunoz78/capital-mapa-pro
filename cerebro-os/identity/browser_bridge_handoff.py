from __future__ import annotations

def build_bridge_handoff(*,access_plan:dict,session:dict,guard:dict,request_id:str,audit_ref:str)->dict:
    required=(request_id,audit_ref)
    if not all(str(x).strip() for x in required):
        raise ValueError("request_id and audit_ref required")
    if access_plan.get("status")!="GREEN":
        return {"status":"BLOCKED","reason":"ACCESS_PLAN_NOT_GREEN","dispatch_candidate":None}
    if access_plan.get("decision")!="COMPUTER_USE_FALLBACK":
        return {"status":"BLOCKED","reason":"COMPUTER_USE_NOT_SELECTED","dispatch_candidate":None}
    if not session.get("authenticated"):
        return {"status":"BLOCKED","reason":"AUTHENTICATED_SESSION_REQUIRED","dispatch_candidate":None}
    if guard.get("status")!="GREEN" or not guard.get("execution_allowed"):
        return {"status":"BLOCKED","reason":"EXECUTION_GUARD_NOT_GREEN","dispatch_candidate":None}

    company_id=str(access_plan.get("company_id","")).strip()
    account_id=str(access_plan.get("account_id","")).strip()
    identity_id=str(access_plan.get("identity_id","")).strip()
    for source,label in ((session,"session"),(guard,"guard")):
        if str(source.get("company_id",company_id))!=company_id:
            raise ValueError(f"cross-company {label} handoff denied")
        if source.get("account_id") not in {None,account_id}:
            raise ValueError(f"cross-account {label} handoff denied")

    profile_id=str(session.get("profile_id","")).strip()
    device_id=str(session.get("device_id","")).strip()
    if not profile_id or not device_id:
        return {"status":"BLOCKED","reason":"PROFILE_DEVICE_REQUIRED","dispatch_candidate":None}

    return {
      "status":"GREEN",
      "reason":None,
      "dispatch_candidate":{
        "request_id":request_id,
        "company_id":company_id,
        "identity_id":identity_id,
        "account_id":account_id,
        "engine_id":str(access_plan.get("engine_id","")).strip(),
        "capability":str(access_plan.get("capability","")).strip(),
        "action":str(access_plan.get("action","")).strip(),
        "device_id":device_id,
        "profile_id":profile_id,
        "environment":str(access_plan.get("environment","LAB")),
        "version":str(access_plan.get("version","1.0.0")),
        "idempotency_key":str(guard.get("idempotency_key","")).strip(),
        "audit_ref":audit_ref,
        "policy_green":True,
        "confidence":float(access_plan.get("confidence",1.0) or 1.0),
        "credential_reference_available":bool(access_plan.get("credential_reference_available")),
      },
      "credential_value_included":False,
      "secret_value_included":False,
      "external_mutation_performed":False,
    }
