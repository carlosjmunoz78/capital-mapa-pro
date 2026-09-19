from __future__ import annotations

def evaluate_access_health(*,company_id:str,environment:str,version:str,accounts:list[dict],sessions:list[dict],credentials:list[dict],connectors:list[dict],bridge_heartbeats:list[dict])->dict:
    if not all(str(x).strip() for x in (company_id,environment,version)):
        raise ValueError("access health scope required")
    if environment not in {"LAB","PREPROD","PROD"}:
        raise ValueError("invalid environment")

    issues=[]
    evidence=[]
    account_ids=set()
    for row in accounts:
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company account evidence denied")
        if row.get("environment") not in {None,environment}:
            continue
        aid=str(row.get("account_id","")).strip()
        if aid:
            account_ids.add(aid)
        if str(row.get("status","ACTIVE")).upper()!="ACTIVE":
            issues.append({"type":"ACCOUNT_INACTIVE","account_id":aid})
        ref=str(row.get("evidence_ref") or "").strip()
        if ref: evidence.append(ref)

    authenticated_accounts=set()
    for row in sessions:
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company session evidence denied")
        if row.get("environment") not in {None,environment}:
            continue
        aid=str(row.get("account_id","")).strip()
        if row.get("authenticated") and aid:
            authenticated_accounts.add(aid)
        ref=str(row.get("evidence_ref") or "").strip()
        if ref: evidence.append(ref)

    credential_accounts=set()
    for row in credentials:
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company credential evidence denied")
        if row.get("environment") not in {None,environment}:
            continue
        aid=str(row.get("account_id","")).strip()
        if aid:
            credential_accounts.add(aid)
        if row.get("secret_value_exposed"):
            issues.append({"type":"SECRET_EXPOSURE","account_id":aid})
        ref=str(row.get("evidence_ref") or "").strip()
        if ref: evidence.append(ref)

    connector_accounts=set()
    for row in connectors:
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company connector evidence denied")
        if row.get("environment") not in {None,environment}:
            continue
        aid=str(row.get("account_id","")).strip()
        if aid:
            connector_accounts.add(aid)
        ref=str(row.get("evidence_ref") or "").strip()
        if ref: evidence.append(ref)

    online_profiles=set()
    for row in bridge_heartbeats:
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company heartbeat evidence denied")
        if row.get("environment") not in {None,environment}:
            continue
        if row.get("online") and row.get("paired") and row.get("kill_switch_enabled"):
            profile=str(row.get("profile_id","")).strip()
            if profile: online_profiles.add(profile)
        ref=str(row.get("evidence_ref") or "").strip()
        if ref: evidence.append(ref)

    for aid in sorted(account_ids):
        if aid not in credential_accounts:
            issues.append({"type":"CREDENTIAL_REF_MISSING","account_id":aid})
        if aid not in authenticated_accounts:
            issues.append({"type":"AUTHENTICATED_SESSION_MISSING","account_id":aid})

    security_incident=any(x["type"]=="SECRET_EXPOSURE" for x in issues)
    if security_incident:
        status="HUMAN_REQUIRED"; human_reason="SECURITY_INCIDENT"
    elif issues:
        status="DEGRADED"; human_reason=None
    else:
        status="GREEN"; human_reason=None

    return {
      "record_type":"access_health_snapshot","company_id":company_id,"environment":environment,"version":version,
      "status":status,"human_reason":human_reason,"accounts_total":len(account_ids),
      "authenticated_accounts":len(authenticated_accounts & account_ids),
      "credentialed_accounts":len(credential_accounts & account_ids),
      "connector_account_count":len(connector_accounts & account_ids),
      "online_bridge_profiles":len(online_profiles),
      "issues":issues,"evidence_refs":tuple(sorted(set(evidence))),
      "prod_actions_allowed":False,"secret_value_exposure_allowed":False,"cost_eur":0.0,
    }

def access_recovery_plan(snapshot:dict)->dict:
    if snapshot.get("status")=="HUMAN_REQUIRED":
        return {
          "status":"HUMAN_REQUIRED","human_reason":snapshot.get("human_reason"),
          "safe_actions":(),"blocked_actions":("AUTONOMOUS_RECOVERY",),
        }
    actions=[]
    for issue in snapshot.get("issues",[]):
        typ=issue.get("type")
        aid=issue.get("account_id")
        if typ=="AUTHENTICATED_SESSION_MISSING":
            actions.append({"action":"SESSION_DISCOVERY_OR_SAFE_RENEWAL","account_id":aid,"auto_safe":True})
        elif typ=="CREDENTIAL_REF_MISSING":
            actions.append({"action":"CREDENTIAL_REFERENCE_AUDIT","account_id":aid,"auto_safe":True})
        elif typ=="ACCOUNT_INACTIVE":
            actions.append({"action":"ACCOUNT_LIFECYCLE_AUDIT","account_id":aid,"auto_safe":True})
    return {
      "status":"GREEN" if not actions else "DEGRADED",
      "human_reason":None,"safe_actions":tuple(actions),"blocked_actions":(),
    }
