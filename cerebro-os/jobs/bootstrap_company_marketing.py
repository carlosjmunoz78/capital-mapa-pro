from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="MKTBOOT-001"
REQUIRED_SOURCES={"BMD-001","KW-001"}

def bootstrap_marketing(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("marketing input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company marketing input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    facts=by_engine.get("BMD-001",{}).get("facts") or {}
    keywords=by_engine.get("KW-001",{}).get("keywords") or []
    personas=[{"segment":str(x),"source":"BMD-001"} for x in (facts.get("target_customers") or [])[:10]]
    organic=[{"keyword":str(x.get("keyword","")),"intent":x.get("intent","DISCOVERY")} for x in keywords[:20] if str(x.get("keyword","")).strip()]
    funnel={"awareness":"organic_content","consideration":"evidence_based_assets","conversion":"existing_authorized_channels","retention":"existing_customer_processes"}
    canonical=json.dumps({"company_id":company_id,"personas":personas,"organic":organic,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"marketing_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB","version":str(payload.get("version","1.0.0")),
      "personas":personas,"organic_opportunities":organic,"funnel":funnel,"missing_sources":missing,
      "status":"GREEN" if not missing and (personas or organic) else "PARTIAL" if personas or organic else "WAITING",
      "default_budget_eur":0.0,"paid_campaigns_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["POL-001","FINOPS-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_MKTBOOT_REQUEST_ROOT",".cerebro-runtime/mktboot-requests"))
    out=Path(os.environ.get("CEREBRO_MKTBOOT_RESULT_ROOT",".cerebro-runtime/mktboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_marketing(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
