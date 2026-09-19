from __future__ import annotations

import json
import os
from pathlib import Path

def assess(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    environment=str(payload.get("environment","LAB")).strip().upper()
    if not company_id:
        raise ValueError("company_id required")
    backup_ok=bool(payload.get("backup_ok",False))
    rebuild_ok=bool(payload.get("rebuild_ok",False))
    supervisor_ok=bool(payload.get("supervisor_ok",False))
    critical_dependency_down=bool(payload.get("critical_dependency_down",False))
    known_safe_failover=bool(payload.get("known_safe_failover",False))
    if critical_dependency_down and environment=="PROD":
        return {
            "company_id":company_id,"engine_id":"BCP-001","environment":environment,
            "status":"HUMAN_REQUIRED","human_reason":"HIGH_RISK",
            "failover_allowed":False,"external_mutation_allowed":False,
        }
    ready=backup_ok and rebuild_ok and supervisor_ok
    failover_allowed=ready and critical_dependency_down and known_safe_failover and environment!="PROD"
    return {
        "company_id":company_id,
        "engine_id":"BCP-001",
        "environment":environment,
        "status":"READY" if ready else "DEGRADED",
        "backup_ok":backup_ok,
        "rebuild_ok":rebuild_ok,
        "supervisor_ok":supervisor_ok,
        "critical_dependency_down":critical_dependency_down,
        "known_safe_failover":known_safe_failover,
        "failover_allowed":failover_allowed,
        "failover_performed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    source_root=Path(os.environ.get("CEREBRO_CONTINUITY_CASE_ROOT",".cerebro-runtime/continuity-cases"))
    out_root=Path(os.environ.get("CEREBRO_CONTINUITY_RESULT_ROOT",".cerebro-runtime/continuity-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("continuity case must be object")
        result=assess(payload)
        target=out_root/f'{result["company_id"]}.{path.stem}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
