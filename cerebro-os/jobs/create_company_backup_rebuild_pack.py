from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="COMP-BKP-001"

def create_backup_rebuild_pack(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    environment=str(payload.get("environment","PREPROD")).upper()
    version=str(payload.get("version","1.0.0"))
    backup=payload.get("backup_evidence") or {}
    rebuild=payload.get("rebuild_evidence") or {}
    for item,label in ((backup,"backup"),(rebuild,"rebuild")):
        if item and str(item.get("company_id",""))!=company_id: raise ValueError(f"cross-company {label} evidence denied")
    backup_green=str(backup.get("status","")).upper()=="GREEN"
    rebuild_green=str(rebuild.get("status","")).upper()=="GREEN"
    restore_rehearsal_green=str((backup.get("rehearsal") or {}).get("status",backup.get("restore_status",""))).upper()=="GREEN"
    checks={
      "backup_green":backup_green,
      "restore_rehearsal_green":restore_rehearsal_green,
      "rebuild_green":rebuild_green,
      "live_restore_performed":bool(backup.get("live_restore_performed",False)),
      "prod_rebuild_performed":bool(rebuild.get("environment")=="PROD" and rebuild.get("rebuild_performed")),
    }
    green=backup_green and restore_rehearsal_green and rebuild_green and not checks["live_restore_performed"] and not checks["prod_rebuild_performed"]
    canonical=json.dumps({"company_id":company_id,"environment":environment,"version":version,"checks":checks},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_backup_rebuild_pack","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":environment,"version":version,"checks":checks,"status":"GREEN" if green else "BLOCKED",
      "live_restore_allowed":False,"prod_rebuild_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_engines":["DR-001","RBLD-001"],"required_gates":["TENANT-001","QA-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_COMPBKP_REQUEST_ROOT",".cerebro-runtime/company-backup-pack-requests"))
    out=Path(os.environ.get("CEREBRO_COMPBKP_RESULT_ROOT",".cerebro-runtime/company-backup-packs")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=create_backup_rebuild_pack(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
