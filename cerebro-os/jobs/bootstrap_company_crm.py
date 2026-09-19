from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="CRMBOOT-001"
REQUIRED_SOURCES={"BMD-001","PROC-001","MKTBOOT-001"}

def bootstrap_crm(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(inputs,list): raise ValueError("inputs must be list")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("CRM input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company CRM input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    processes=by_engine.get("PROC-001",{}).get("processes") or []
    facts=by_engine.get("BMD-001",{}).get("facts") or {}
    personas=by_engine.get("MKTBOOT-001",{}).get("personas") or []
    entities=[
      {"name":"lead","source":"canonical","required":True},
      {"name":"customer","source":"canonical","required":True},
      {"name":"opportunity","source":"canonical","required":True},
      {"name":"activity","source":"canonical","required":True},
    ]
    pipeline=[]
    for row in processes[:25]:
        name=str(row.get("name","")).strip()
        if name: pipeline.append({"stage_candidate":name,"source_process_id":row.get("process_id"),"candidate_only":True})
    segments=[str(x.get("segment","")).strip() for x in personas if str(x.get("segment","")).strip()]
    canonical=json.dumps({"company_id":company_id,"entities":entities,"pipeline":pipeline,"segments":segments,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"crm_bootstrap_candidate","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD",
      "version":str(payload.get("version","1.0.0")),"source_engines":sorted(by_engine),"missing_sources":missing,
      "entities":entities,"pipeline_candidates":pipeline,"customer_segments":segments,
      "status":"GREEN" if not missing else "PARTIAL",
      "existing_crm_preserved":True,"schema_mutation_allowed":False,"prod_write_allowed":False,
      "external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["TENANT-001","DATA-001","QA-001","REG-001","DR-001","RBLD-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_CRMBOOT_REQUEST_ROOT",".cerebro-runtime/crmboot-requests"))
    out=Path(os.environ.get("CEREBRO_CRMBOOT_RESULT_ROOT",".cerebro-runtime/crmboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_crm(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
