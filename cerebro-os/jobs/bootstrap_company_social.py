from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="SOCBOOT-001"
REQUIRED_SOURCES={"SOCAUD-001","BMD-001"}

def bootstrap_social(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("social input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company social input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    profiles=by_engine.get("SOCAUD-001",{}).get("profiles") or []
    facts=by_engine.get("BMD-001",{}).get("facts") or {}
    pillars=[]
    for service in (facts.get("products_services") or [])[:10]:
        pillars.append({"pillar":str(service),"source":"BMD-001"})
    channels=[{"platform":p.get("platform"),"handle_or_url":p.get("handle_or_url"),"mode":"PLAN_ONLY"} for p in profiles]
    canonical=json.dumps({"company_id":company_id,"pillars":pillars,"channels":channels,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"social_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB","version":str(payload.get("version","1.0.0")),
      "pillars":pillars,"channels":channels,"missing_sources":missing,"status":"GREEN" if not missing and (pillars or channels) else "PARTIAL" if pillars or channels else "WAITING",
      "publication_allowed":False,"external_mutation_allowed":False,"paid_distribution_allowed":False,"cost_eur":0.0,
      "required_gates":["POL-001","PRV-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_SOCBOOT_REQUEST_ROOT",".cerebro-runtime/socboot-requests"))
    out=Path(os.environ.get("CEREBRO_SOCBOOT_RESULT_ROOT",".cerebro-runtime/socboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_social(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
