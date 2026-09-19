from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="AUTBOOT-001"
REQUIRED_SOURCES={"PROC-001","CRMBOOT-001","APPBOOT-001"}

def bootstrap_automations(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("automation input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company automation input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    processes=by_engine.get("PROC-001",{}).get("processes") or []
    candidates=[]
    for row in processes[:30]:
        name=str(row.get("name","")).strip()
        if name:
            candidates.append({"name":f"observe_{name.lower().replace(' ','_')[:48]}","trigger":"EVENT_CANDIDATE","action":"NOOP_PREPROD","candidate_only":True,"external_side_effect":False})
    canonical=json.dumps({"company_id":company_id,"candidates":candidates,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"automation_bootstrap_candidate","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD",
      "version":str(payload.get("version","1.0.0")),"automation_candidates":candidates,"missing_sources":missing,
      "status":"GREEN" if not missing else "PARTIAL",
      "live_execution_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["POL-001","TENANT-001","QA-001","REG-001","OBSERV-001","DR-001","RBLD-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_AUTBOOT_REQUEST_ROOT",".cerebro-runtime/autboot-requests"))
    out=Path(os.environ.get("CEREBRO_AUTBOOT_RESULT_ROOT",".cerebro-runtime/autboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_automations(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
