from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="APPBOOT-001"
REQUIRED_SOURCES={"BMD-001","PROC-001","CRMBOOT-001"}

def bootstrap_app(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(inputs,list): raise ValueError("inputs must be list")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("APP input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company APP input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    facts=by_engine.get("BMD-001",{}).get("facts") or {}
    processes=by_engine.get("PROC-001",{}).get("processes") or []
    crm=by_engine.get("CRMBOOT-001",{})
    modules=[{"module":"dashboard","candidate_only":True},{"module":"crm","candidate_only":True}]
    for row in processes[:20]:
        name=str(row.get("name","")).strip()
        if name: modules.append({"module":name.lower().replace(" ","_")[:64],"source_process_id":row.get("process_id"),"candidate_only":True})
    roles=[{"role":"company_operator","source":"default_candidate"}]
    if facts.get("target_customers"): roles.append({"role":"company_manager","source":"business_model_candidate"})
    canonical=json.dumps({"company_id":company_id,"modules":modules,"roles":roles,"crm_hash":crm.get("evidence_hash"),"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"app_bootstrap_candidate","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD",
      "version":str(payload.get("version","1.0.0")),"modules":modules,"role_candidates":roles,"missing_sources":missing,
      "status":"GREEN" if not missing else "PARTIAL",
      "existing_app_preserved":True,"feature_flag_required":True,"prod_deploy_allowed":False,
      "external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["TENANT-001","IAM-001","QA-001","REG-001","CAN-001","DR-001","RBLD-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_APPBOOT_REQUEST_ROOT",".cerebro-runtime/appboot-requests"))
    out=Path(os.environ.get("CEREBRO_APPBOOT_RESULT_ROOT",".cerebro-runtime/appboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_app(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
