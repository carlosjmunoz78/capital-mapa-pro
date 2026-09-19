from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="APPBOOT-001"

def bootstrap_app(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    existing=payload.get("existing_contract_refs") or []
    roles=payload.get("roles") or []
    modules=payload.get("modules") or []
    if not isinstance(existing,list) or not isinstance(roles,list) or not isinstance(modules,list):
        raise ValueError("existing_contract_refs, roles and modules must be lists")
    if not existing:
        return {
          "record_type":"app_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD","version":str(payload.get("version","1.0.0")),
          "status":"BLOCKED","reason":"EXISTING_APP_CONTRACT_INVENTORY_REQUIRED","prod_deploy_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
        }
    plan={"roles":sorted({str(x).strip() for x in roles if str(x).strip()}),"modules":sorted({str(x).strip() for x in modules if str(x).strip()})}
    canonical=json.dumps({"company_id":company_id,"existing":sorted(map(str,existing)),"plan":plan},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"app_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD","version":str(payload.get("version","1.0.0")),
      "status":"GREEN","existing_contract_refs":sorted(map(str,existing)),"plan":plan,"strategy":"EXTEND_EXISTING_OR_ISOLATED_SCAFFOLD",
      "prod_deploy_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["TENANT-001","QA-001","REG-001","SEC-001","DR-001","RBLD-001"],
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
