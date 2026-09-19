from __future__ import annotations
import json, os
from pathlib import Path

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    backup_root=Path(os.environ.get("CEREBRO_BACKUP_RESULT_ROOT",".cerebro-runtime/backup-results"))
    rebuild_root=Path(os.environ.get("CEREBRO_REBUILD_RESULT_ROOT",".cerebro-runtime/rebuild-results"))
    incident_root=Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))
    out_root=Path(os.environ.get("CEREBRO_CONTINUITY_CASE_ROOT",".cerebro-runtime/continuity-cases"))
    out_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        company_id=str(cfg["company_id"]); environment=str(cfg["environment"]).upper()
        backup_ok=False; rebuild_ok=False; supervisor_ok=True; critical=False
        bp=backup_root/f"{company_id}.json"
        if bp.exists():
            b=json.loads(bp.read_text(encoding="utf-8"))
            if str(b.get("company_id",""))!=company_id: raise ValueError("cross-company backup result denied")
            backup_ok=str(b.get("status","")).upper()=="GREEN"
        rp=rebuild_root/f"{company_id}.json"
        if rp.exists():
            r=json.loads(rp.read_text(encoding="utf-8"))
            if str(r.get("company_id",""))!=company_id: raise ValueError("cross-company rebuild result denied")
            rebuild_ok=str(r.get("status","")).upper()=="GREEN"
        ip=incident_root/f"{company_id}.json"
        if ip.exists():
            i=json.loads(ip.read_text(encoding="utf-8"))
            if str(i.get("company_id",""))!=company_id: raise ValueError("cross-company incident result denied")
            critical=any(str(x.get("severity","")).upper()=="CRITICAL" for x in (i.get("incidents") or []))
            supervisor_ok=str(i.get("status","")).upper() not in {"BLOCKED"}
        payload={
            "record_type":"continuity_runtime_case",
            "company_id":company_id,
            "environment":environment,
            "backup_ok":backup_ok,
            "rebuild_ok":rebuild_ok,
            "supervisor_ok":supervisor_ok,
            "critical_dependency_down":critical,
            "known_safe_failover":False,
            "source_engines":["DR-001","RBLD-001","INC-001"],
            "external_mutation_allowed":False,
            "cost_eur":0.0,
        }
        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
