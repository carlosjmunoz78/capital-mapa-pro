from __future__ import annotations

REQUIRED_TRUE_CHECKS=(
    "service_found","service_version","loopback_only","paired","lab_scope",
    "prod_disabled","extension_connected","extension_fresh","transport_online",
)

def evaluate_browser_bridge_acceptance(evidence:dict|None,*,company_id:str)->dict:
    if evidence is None:
        return {
          "status":"ABSENT","decision":"PHYSICAL_ACCEPTANCE_EVIDENCE_REQUIRED",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }
    if not isinstance(evidence,dict):
        raise ValueError("browser bridge acceptance evidence must be object")

    if str(evidence.get("record_type",""))!="cerebro_browser_bridge_acceptance":
        raise ValueError("invalid browser bridge acceptance record_type")
    evidence_company=str(evidence.get("company_id","")).strip()
    if evidence_company!=company_id:
        raise ValueError("cross-company browser bridge acceptance denied")
    if str(evidence.get("environment","")).upper()!="LAB":
        return {
          "status":"BLOCKED","decision":"LAB_SCOPE_REQUIRED",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }

    if bool(evidence.get("external_mutation_allowed",False)):
        return {
          "status":"BLOCKED","decision":"EXTERNAL_MUTATION_FLAG_FORBIDDEN",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }
    if bool(evidence.get("prod_activation_allowed",False)):
        return {
          "status":"BLOCKED","decision":"PROD_FLAG_FORBIDDEN",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }
    if bool(evidence.get("secret_value_included",False)):
        return {
          "status":"HUMAN_REQUIRED","decision":"SECRET_EXPOSURE_DETECTED",
          "human_reason":"SECURITY_INCIDENT",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":False,
        }

    checks=evidence.get("checks") or {}
    if not isinstance(checks,dict):
        raise ValueError("browser bridge acceptance checks must be object")
    if bool(checks.get("raw_secret_exposed",False)):
        return {
          "status":"HUMAN_REQUIRED","decision":"SECRET_EXPOSURE_DETECTED",
          "human_reason":"SECURITY_INCIDENT",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":False,
        }

    missing=tuple(name for name in REQUIRED_TRUE_CHECKS if not bool(checks.get(name,False)))
    if str(evidence.get("status","")).upper()!="GREEN" or missing:
        return {
          "status":"PARTIAL","decision":"PHYSICAL_ACCEPTANCE_NOT_GREEN",
          "blocking_checks":missing,
          "next_gate":str(evidence.get("next_gate") or "PHYSICAL_ACCEPTANCE"),
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }

    device_id=str(evidence.get("device_id","")).strip()
    profile_id=str(evidence.get("profile_id","")).strip()
    service_version=str(evidence.get("service_version","")).strip()
    if not device_id or not profile_id or not service_version:
        return {
          "status":"PARTIAL","decision":"PHYSICAL_ACCEPTANCE_SCOPE_INCOMPLETE",
          "remote_lab_roundtrip_allowed":False,"local_pc_required":True,
        }

    return {
      "status":"GREEN",
      "decision":"REMOTE_LAB_ROUNDTRIP_READY",
      "company_id":company_id,
      "device_id":device_id,
      "profile_id":profile_id,
      "service_version":service_version,
      "environment":"LAB",
      "remote_lab_roundtrip_allowed":True,
      "allowed_remote_action":"OPEN_LOCAL_TEST_PAGE",
      "local_pc_required":False,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }
