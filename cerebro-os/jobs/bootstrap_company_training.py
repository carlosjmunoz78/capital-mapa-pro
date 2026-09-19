from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="TRNBOOT-001"
REQUIRED_SOURCES={"KBOOT-001","BMD-001","PROC-001"}

def bootstrap_training(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("training input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company training input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    knowledge=by_engine.get("KBOOT-001",{}).get("knowledge_candidates") or []
    processes=by_engine.get("PROC-001",{}).get("processes") or []
    cases=[]
    for row in knowledge[:20]:
        cases.append({"case_type":"KNOWLEDGE_RETRIEVAL","source_knowledge_id":row.get("knowledge_id"),"expected":"PROVENANCE_REQUIRED","lab_only":True})
    for row in processes[:20]:
        cases.append({"case_type":"PROCESS_REASONING","source_process_id":row.get("process_id"),"expected":"NO_UNSUPPORTED_ACTION","lab_only":True})
    canonical=json.dumps({"company_id":company_id,"cases":cases,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"training_bootstrap_candidate","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB",
      "version":str(payload.get("version","1.0.0")),"training_cases":cases,"case_count":len(cases),"missing_sources":missing,
      "status":"GREEN" if not missing else "PARTIAL",
      "direct_prod_promotion_allowed":False,"policy_mutation_allowed":False,"permission_mutation_allowed":False,
      "external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["TRN-001","EVA-001","JDG-001","REG-001","TENANT-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_TRNBOOT_REQUEST_ROOT",".cerebro-runtime/trnboot-requests"))
    out=Path(os.environ.get("CEREBRO_TRNBOOT_RESULT_ROOT",".cerebro-runtime/trnboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_training(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
