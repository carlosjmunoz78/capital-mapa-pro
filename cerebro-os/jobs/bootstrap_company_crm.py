from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="CRMBOOT-001"

def bootstrap_crm(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    existing=payload.get("existing_contract_refs") or []
    entities=payload.get("entities") or []
    pipeline=payload.get("pipeline") or []
    if not isinstance(existing,list) or not isinstance(entities,list) or not isinstance(pipeline,list):
        raise ValueError("existing_contract_refs, entities and pipeline must be lists")
    if not existing:
        return {
          "record_type":"crm_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD","version":str(payload.get("version","1.0.0")),
          "status":"BLOCKED","reason":"EXISTING_CONTRACT_INVENTORY_REQUIRED","existing_contract_refs":[],
          "migration_allowed":False,"prod_write_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
        }
    normalized_entities=sorted({str(x).strip() for x in entities if str(x).strip()})
    normalized_pipeline=sorted({str(x).strip() for x in pipeline if str(x).strip()})
    canonical=json.dumps({"company_id":company_id,"existing":sorted(map(str,existing)),"entities":normalized_entities,"pipeline":normalized_pipeline},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"crm_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD","version":str(payload.get("version","1.0.0")),
      "status":"GREEN","existing_contract_refs":sorted(map(str,existing)),"entities":normalized_entities,"pipeline":normalized_pipeline,
      "strategy":"WRAP_EXISTING_FIRST","migration_allowed":False,"prod_write_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["DATA-001","TENANT-001","QA-001","REG-001","DR-001","RBLD-001"],
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
