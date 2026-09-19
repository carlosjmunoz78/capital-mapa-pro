from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

def _incident_id(company_id:str,incident_type:str,evidence_ref:str)->str:
    raw="|".join([company_id,incident_type,evidence_ref])
    return "inc-"+hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def _incident(company_id:str,environment:str,version:str,incident_type:str,severity:str,evidence_ref:str,repair_id:str|None=None,human_reason:str|None=None)->dict:
    return {
        "incident_id":_incident_id(company_id,incident_type,evidence_ref),
        "company_id":company_id,
        "engine_id":"INC-001",
        "environment":environment,
        "version":version,
        "incident_type":incident_type,
        "severity":severity,
        "status":"HUMAN_REQUIRED" if human_reason else "OPEN",
        "human_reason":human_reason,
        "evidence_ref":evidence_ref,
        "known_incident":bool(repair_id) and not human_reason,
        "preapproved_repair_id":repair_id,
        "containment_required":severity in {"HIGH","CRITICAL"},
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def detect_for_company(company_id:str,environment:str,version:str)->dict:
    if not all((company_id.strip(),environment.strip(),version.strip())):
        raise ValueError("complete incident scope required")
    rag_root=Path(os.environ.get("CEREBRO_RAG_INDEX_ROOT",".cerebro-runtime/rag-index"))
    twin_root=Path(os.environ.get("CEREBRO_DIGITAL_TWIN_ROOT",".cerebro-runtime/digital-twin"))
    inventory_root=Path(os.environ.get("CEREBRO_KNOWLEDGE_INVENTORY_ROOT",".cerebro-runtime/knowledge-inventory"))
    red_root=Path(os.environ.get("CEREBRO_RED_TEAM_SUMMARY_ROOT",".cerebro-runtime/red-team-summary"))
    regression_root=Path(os.environ.get("CEREBRO_REGRESSION_ROOT",".cerebro-runtime/regression"))
    process_root=Path(os.environ.get("CEREBRO_PROCESS_QA_RESULT_ROOT",".cerebro-runtime/process-qa-results"))

    incidents=[]
    inventory=inventory_root/f"{company_id}.json"
    rag=rag_root/f"{company_id}.json"
    twin=twin_root/f"{company_id}.snapshot.json"
    if environment!="PROD" and inventory.exists() and not rag.exists():
        incidents.append(_incident(company_id,environment,version,"RAG_INDEX_MISSING","MEDIUM",str(rag),"REBUILD_RAG_INDEX"))
    if environment!="PROD" and not twin.exists():
        incidents.append(_incident(company_id,environment,version,"TWIN_SNAPSHOT_MISSING","LOW",str(twin),"REBUILD_TWIN_SNAPSHOT"))

    red=red_root/f"{company_id}.json"
    if red.exists():
        payload=json.loads(red.read_text(encoding="utf-8"))
        if str(payload.get("company_id","")) not in {"",company_id}:
            raise ValueError("cross-company red-team evidence denied")
        if str(payload.get("status","")).upper()=="RED":
            incidents.append(_incident(company_id,environment,version,"SECURITY_REGRESSION","CRITICAL",str(red),None,"SECURITY_INCIDENT"))

    for path in sorted(regression_root.glob(f"{company_id}.*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if str(payload.get("company_id",""))!=company_id:
            raise ValueError("cross-company regression evidence denied")
        if str(payload.get("status","")).upper()=="BLOCKED":
            incidents.append(_incident(company_id,environment,version,"BEHAVIOR_REGRESSION","HIGH",str(path),None,"HIGH_RISK"))

    for path in sorted(process_root.glob(f"{company_id}.*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if str(payload.get("company_id",""))!=company_id:
            raise ValueError("cross-company process QA evidence denied")
        status=str(payload.get("status","")).upper()
        if status=="HUMAN_REQUIRED":
            incidents.append(_incident(company_id,environment,version,"CRITICAL_PROCESS_NON_CONFORMITY","CRITICAL",str(path),None,str(payload.get("human_reason") or "HIGH_RISK")))
        elif status=="NON_CONFORMITY":
            incidents.append(_incident(company_id,environment,version,"PROCESS_NON_CONFORMITY","MEDIUM",str(path),None,None))

    return {
        "record_type":"incident_detection_result",
        "company_id":company_id,
        "engine_id":"INC-001",
        "environment":environment,
        "version":version,
        "incident_count":len(incidents),
        "incidents":incidents,
        "status":"HUMAN_REQUIRED" if any(x["status"]=="HUMAN_REQUIRED" for x in incidents) else "OPEN" if incidents else "GREEN",
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    out_root=Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))
    out_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        company_id=str(cfg["company_id"]); environment=str(cfg["environment"]); version=str(cfg["version"])
        result=detect_for_company(company_id,environment,version)
        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
