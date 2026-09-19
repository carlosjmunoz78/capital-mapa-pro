from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="ENGACT-001"
BASE_REQUIRED=("COMP-REG-001","COMP-ONB-001","ACCESSBOOT-001","TENANT-001","OBSERV-001","DR-001","RBLD-001")
DISCOVERY_REQUIRED=("SCAN-001","BMD-001","PROC-001","WAUD-001","KW-001","SOCAUD-001","LOCALP-001","COMPET-001","KBOOT-001")
PLAN_REQUIRED=("SEOBOOT-001","SOCBOOT-001","MKTBOOT-001")

def activate_matrix(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    evidence=payload.get("engine_evidence") or []
    if not isinstance(evidence,list): raise ValueError("engine_evidence must be list")
    observed={}
    for item in evidence:
        if not isinstance(item,dict): raise ValueError("engine evidence must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company engine evidence denied")
        eid=str(item.get("engine_id","")).strip()
        if eid: observed[eid]=str(item.get("status","UNKNOWN"))
    matrix=[]
    for eid in BASE_REQUIRED+DISCOVERY_REQUIRED+PLAN_REQUIRED:
        status=observed.get(eid,"MISSING")
        matrix.append({"engine_id":eid,"required":True,"evidence_status":status,"activation_status":"READY_CANDIDATE" if status=="GREEN" else "BLOCKED"})
    blocked=[x["engine_id"] for x in matrix if x["activation_status"]=="BLOCKED"]
    canonical=json.dumps({"company_id":company_id,"matrix":matrix},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_engine_activation_matrix","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB","version":str(payload.get("version","1.0.0")),
      "matrix":matrix,"blocked_required_engines":blocked,"status":"GREEN" if not blocked else "PARTIAL",
      "prod_activation_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "next_stage":"CRM_APP_AUTOMATION_TRAINING_BOOTSTRAPS" if not blocked else "RESOLVE_DISCOVERY_OR_PLAN_GAPS",
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_ENGACT_REQUEST_ROOT",".cerebro-runtime/engact-requests"))
    out=Path(os.environ.get("CEREBRO_ENGACT_RESULT_ROOT",".cerebro-runtime/engact-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=activate_matrix(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
