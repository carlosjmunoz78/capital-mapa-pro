from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="COMP-DEP-001"
REQUIRED_EVIDENCE=("COMP-HLT-001","COMP-BKP-001","QA-001","QAB-001","REG-001","TENANT-001","EVA-001","JDG-001","TWIN-001","RED-001","BCP-001","OBSERV-001","DR-001","RBLD-001")

def evaluate_preprod_readiness(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    evidence=payload.get("engine_evidence") or []
    if not isinstance(evidence,list): raise ValueError("engine_evidence must be list")
    observed={}
    for item in evidence:
        if not isinstance(item,dict): raise ValueError("engine evidence must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company preprod evidence denied")
        eid=str(item.get("engine_id","")).strip()
        if eid: observed[eid]=str(item.get("status","UNKNOWN")).upper()
    missing=[eid for eid in REQUIRED_EVIDENCE if eid not in observed]
    not_green=[eid for eid in REQUIRED_EVIDENCE if observed.get(eid) not in {None,"GREEN"}]
    ready=not missing and not not_green
    canonical=json.dumps({"company_id":company_id,"observed":observed,"missing":missing,"not_green":not_green},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_preprod_readiness","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":"PREPROD","version":str(payload.get("version","1.0.0")),
      "required_evidence":list(REQUIRED_EVIDENCE),"missing_evidence":missing,"not_green":not_green,
      "status":"GREEN" if ready else "BLOCKED","preprod_ready":ready,
      "production_activation_allowed":False,"canary_live_traffic_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "next_stage":"PRODUCTION_ACTIVATION_GATE_ONLY" if ready else "RESOLVE_PREPROD_GAPS",
      "human_required_if_prod_requested":"HIGH_RISK",
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_COMPDEP_REQUEST_ROOT",".cerebro-runtime/company-deploy-requests"))
    out=Path(os.environ.get("CEREBRO_COMPDEP_RESULT_ROOT",".cerebro-runtime/company-deploy-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=evaluate_preprod_readiness(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
