from __future__ import annotations

import json
import os
from pathlib import Path

SEVERITY_ORDER={"LOW":1,"MEDIUM":2,"HIGH":3,"CRITICAL":4}

def evaluate_process(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    process_id=str(payload.get("process_id","")).strip()
    environment=str(payload.get("environment","LAB")).strip().upper()
    version=str(payload.get("version","1.0.0")).strip()
    if not all((company_id,process_id,environment,version)):
        raise ValueError("complete process scope required")
    checks=payload.get("checks")
    if not isinstance(checks,list) or not checks:
        raise ValueError("process checks required")
    findings=[]
    for check in checks:
        if not isinstance(check,dict): raise ValueError("process check must be object")
        check_id=str(check.get("check_id","")).strip()
        status=str(check.get("status","")).strip().upper()
        severity=str(check.get("severity","MEDIUM")).strip().upper()
        if not check_id or status not in {"GREEN","RED"} or severity not in SEVERITY_ORDER:
            raise ValueError("invalid process check")
        if status=="RED":
            findings.append({
                "check_id":check_id,
                "severity":severity,
                "reason":str(check.get("reason","PROCESS_NON_CONFORMITY")),
                "evidence_ref":str(check.get("evidence_ref","")),
            })
    highest=max((SEVERITY_ORDER[f["severity"]] for f in findings),default=0)
    status="GREEN" if not findings else "HUMAN_REQUIRED" if highest>=4 else "NON_CONFORMITY"
    return {
        "record_type":"business_process_qa_result",
        "company_id":company_id,
        "engine_id":"QAB-001",
        "process_id":process_id,
        "environment":environment,
        "version":version,
        "status":status,
        "non_conformities":findings,
        "non_conformity_count":len(findings),
        "human_reason":"HIGH_RISK" if highest>=4 else None,
        "auto_mutation_allowed":False,
        "external_mutation_allowed":False,
        "production_ready":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    source_root=Path(os.environ.get("CEREBRO_PROCESS_QA_CASE_ROOT",".cerebro-runtime/process-qa-cases"))
    out_root=Path(os.environ.get("CEREBRO_PROCESS_QA_RESULT_ROOT",".cerebro-runtime/process-qa-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("process QA case must be object")
        result=evaluate_process(payload)
        target=out_root/f'{result["company_id"]}.{result["process_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
