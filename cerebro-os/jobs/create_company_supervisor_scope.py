from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from multicompany.health import company_health

ENGINE_ID="COMP-HLT-001"
DEFAULT_REQUIRED=("COMP-REG-001","COMP-ONB-001","TENANT-001","CRMBOOT-001","APPBOOT-001","AUTBOOT-001","TRNBOOT-001","ACCESS-HLT-001")

def create_supervisor_scope(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    environment=str(payload.get("environment","PREPROD")).upper()
    version=str(payload.get("version","1.0.0"))
    evidence=payload.get("engine_evidence") or []
    if not isinstance(evidence,list): raise ValueError("engine_evidence must be list")
    states={}; refs={}; scopes={}
    for item in evidence:
        if not isinstance(item,dict): raise ValueError("engine evidence must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company supervisor evidence denied")
        eid=str(item.get("engine_id","")).strip()
        if not eid: continue
        states[eid]=str(item.get("status","UNKNOWN")).upper()
        ref=str(item.get("evidence_hash") or item.get("evidence_ref") or "").strip()
        refs[eid]=[ref] if ref else []
        scopes[eid]={"company_id":company_id,"environment":str(item.get("environment",environment)).upper(),"version":str(item.get("version",version))}
    required=tuple(payload.get("required_engines") or DEFAULT_REQUIRED)
    health=company_health(company_id=company_id,required_engines=required,engine_states=states,evidence_refs=refs,environment=environment,version=version,evidence_scopes=scopes)
    canonical=json.dumps({"company_id":company_id,"environment":environment,"version":version,"required":required,"health":health},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_supervisor_scope","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":environment,"version":version,"required_engines":list(required),"health":health,
      "status":"GREEN" if health["state"]=="GREEN" else health["state"],
      "prod_actions_allowed":False,"self_heal_prod_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["OBSERV-001","INC-001","SELF-001","TENANT-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_COMPHLT_REQUEST_ROOT",".cerebro-runtime/company-health-requests"))
    out=Path(os.environ.get("CEREBRO_COMPHLT_RESULT_ROOT",".cerebro-runtime/company-health-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=create_supervisor_scope(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
