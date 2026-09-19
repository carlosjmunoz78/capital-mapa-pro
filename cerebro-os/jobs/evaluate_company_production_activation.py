from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="COMP-DEP-001"
REQUIRED_SOURCE="COMP-DEP-001"

def evaluate_production_activation(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    readiness=payload.get("preprod_readiness") or {}
    if not isinstance(readiness,dict): raise ValueError("preprod_readiness must be object")
    if str(readiness.get("company_id",""))!=company_id:
        raise ValueError("cross-company production readiness denied")
    if str(readiness.get("engine_id",""))!=REQUIRED_SOURCE:
        raise ValueError("COMP-DEP-001 preprod readiness required")
    preprod_green=str(readiness.get("status","")).upper()=="GREEN" and bool(readiness.get("preprod_ready"))
    canonical=json.dumps({"company_id":company_id,"readiness_hash":readiness.get("evidence_hash"),"preprod_green":preprod_green},sort_keys=True,separators=(",",":"))
    if not preprod_green:
        return {
          "record_type":"company_production_activation_gate","company_id":company_id,"engine_id":"COMP-ONB-001",
          "phase":"PRODUCTION_ACTIVATION","environment":"PREPROD","version":str(payload.get("version","1.0.0")),
          "status":"BLOCKED","reason":"PREPROD_NOT_GREEN","human_reason":None,
          "production_activation_allowed":False,"external_mutation_allowed":False,"live_traffic_allowed":False,"cost_eur":0.0,
          "required_evidence":["COMP-DEP-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
        }
    return {
      "record_type":"company_production_activation_gate","company_id":company_id,"engine_id":"COMP-ONB-001",
      "phase":"PRODUCTION_ACTIVATION","environment":"PREPROD","version":str(payload.get("version","1.0.0")),
      "status":"HUMAN_REQUIRED","reason":"PROD_ACTIVATION_REQUIRES_EXPLICIT_HIGH_RISK_GATE","human_reason":"HIGH_RISK",
      "production_activation_allowed":False,"external_mutation_allowed":False,"live_traffic_allowed":False,"cost_eur":0.0,
      "required_evidence":["COMP-DEP-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_PROD_ACTIVATION_REQUEST_ROOT",".cerebro-runtime/company-prod-activation-requests"))
    out=Path(os.environ.get("CEREBRO_PROD_ACTIVATION_RESULT_ROOT",".cerebro-runtime/company-prod-activation-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=evaluate_production_activation(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
