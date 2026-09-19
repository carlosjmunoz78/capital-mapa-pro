from __future__ import annotations

import json
import os
from pathlib import Path

CRISIS_TYPES={
    "WEB_DOWN":{"default_severity":"HIGH","human_reason":"HIGH_RISK","playbook":["FREEZE_DEPLOYMENTS","CHECK_LAST_GREEN","PREPARE_STATUS_DRAFT"]},
    "DATA_LEAK":{"default_severity":"CRITICAL","human_reason":"SECURITY_INCIDENT","playbook":["CONTAIN_ACCESS","PRESERVE_EVIDENCE","PREPARE_SECURITY_NOTIFICATION_DRAFT"]},
    "REPUTATION_CRISIS":{"default_severity":"HIGH","human_reason":"HIGH_RISK","playbook":["FREEZE_AUTOREPLIES","PRESERVE_CONTEXT","PREPARE_COMMS_DRAFT"]},
    "BANK_BLOCKED":{"default_severity":"HIGH","human_reason":"HIGH_RISK","playbook":["PAUSE_BANK_ROUTING","PRESERVE_CASES","PREPARE_ALTERNATIVE_ROUTING_DRAFT"]},
    "LEGAL_INCIDENT":{"default_severity":"CRITICAL","human_reason":"LEGAL_REQUIRED","playbook":["FREEZE_SENSITIVE_ACTIONS","PRESERVE_EVIDENCE","PREPARE_LEGAL_HANDOFF"]},
    "MASS_FAILURE":{"default_severity":"CRITICAL","human_reason":"HIGH_RISK","playbook":["ENTER_DEGRADED_MODE","FREEZE_RISKY_WRITES","PRESERVE_EVIDENCE"]},
}

def classify(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    crisis_type=str(payload.get("crisis_type","")).strip().upper()
    environment=str(payload.get("environment","LAB")).strip().upper()
    version=str(payload.get("version","1.0.0")).strip()
    if not all((company_id,crisis_type,environment,version)):
        raise ValueError("complete crisis scope required")
    if crisis_type not in CRISIS_TYPES:
        raise ValueError("unsupported crisis type")
    spec=CRISIS_TYPES[crisis_type]
    severity=str(payload.get("severity",spec["default_severity"])).strip().upper()
    if severity not in {"LOW","MEDIUM","HIGH","CRITICAL"}:
        raise ValueError("invalid crisis severity")
    high=severity in {"HIGH","CRITICAL"}
    human_reason=spec["human_reason"] if high else None
    actions=[]
    for action in spec["playbook"]:
        actions.append({
            "action":action,
            "status":"PREPARED_ONLY",
            "external_execution_allowed":False,
            "communication_send_allowed":False,
            "requires_policy_gate":True,
        })
    return {
        "record_type":"crisis_response_plan",
        "company_id":company_id,
        "engine_id":"CRS-001",
        "environment":environment,
        "version":version,
        "crisis_type":crisis_type,
        "severity":severity,
        "status":"HUMAN_REQUIRED" if high else "PLAN_READY",
        "human_reason":human_reason,
        "actions":actions,
        "containment_mode":"FAIL_CLOSED",
        "external_mutation_allowed":False,
        "external_communication_sent":False,
        "production_ready":False,
        "cost_eur":0.0,
    }

def derive_from_incidents(incident_payload:dict)->list[dict]:
    company_id=str(incident_payload.get("company_id","")).strip()
    environment=str(incident_payload.get("environment","LAB")).strip().upper()
    version=str(incident_payload.get("version","1.0.0")).strip()
    if not company_id:
        raise ValueError("company_id required")
    derived=[]
    for incident in incident_payload.get("incidents") or []:
        if str(incident.get("company_id",""))!=company_id:
            raise ValueError("cross-company incident denied")
        itype=str(incident.get("incident_type","")).upper()
        severity=str(incident.get("severity","MEDIUM")).upper()
        if itype=="SECURITY_REGRESSION":
            crisis_type="DATA_LEAK"
        elif itype in {"BEHAVIOR_REGRESSION","CRITICAL_PROCESS_NON_CONFORMITY"} and severity=="CRITICAL":
            crisis_type="MASS_FAILURE"
        else:
            continue
        derived.append(classify({
            "company_id":company_id,
            "environment":environment,
            "version":version,
            "crisis_type":crisis_type,
            "severity":severity,
        }))
    return derived

def run()->list[Path]:
    incident_root=Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))
    out_root=Path(os.environ.get("CEREBRO_CRISIS_ROOT",".cerebro-runtime/crisis"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(incident_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict):
            raise ValueError("incident payload must be object")
        company_id=str(payload.get("company_id","")).strip()
        plans=derive_from_incidents(payload)
        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"crisis_company_snapshot",
            "company_id":company_id,
            "engine_id":"CRS-001",
            "plans":plans,
            "status":"HUMAN_REQUIRED" if any(p["status"]=="HUMAN_REQUIRED" for p in plans) else "GREEN",
            "external_mutation_allowed":False,
            "external_communication_sent":False,
            "cost_eur":0.0,
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
