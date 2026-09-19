from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="SEOBOOT-001"
REQUIRED_SOURCES={"WAUD-001","KW-001"}

def bootstrap_seo(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(inputs,list): raise ValueError("inputs must be list")
    by_engine={}
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("SEO input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company SEO input denied")
        by_engine[str(item.get("engine_id",""))]=item
    missing=sorted(REQUIRED_SOURCES-set(by_engine))
    kw=by_engine.get("KW-001",{}).get("keywords") or []
    waud=by_engine.get("WAUD-001",{})
    actions=[]
    for row in kw[:25]:
        term=str(row.get("keyword","")).strip()
        if term: actions.append({"type":"KEYWORD_TARGET_CANDIDATE","keyword":term,"intent":row.get("intent","DISCOVERY"),"publish_allowed":False})
    if int(waud.get("issue_count",0) or 0)>0:
        actions.append({"type":"TECHNICAL_AUDIT_REMEDIATION_CANDIDATE","issue_count":int(waud.get("issue_count",0)),"publish_allowed":False})
    canonical=json.dumps({"company_id":company_id,"actions":actions,"missing":missing},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"seo_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB",
      "version":str(payload.get("version","1.0.0")),"source_engines":sorted(by_engine),"missing_sources":missing,
      "actions":actions,"action_count":len(actions),"status":"GREEN" if not missing and actions else "PARTIAL" if actions else "WAITING",
      "publication_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["POL-001","QA-001","PRV-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_SEOBOOT_REQUEST_ROOT",".cerebro-runtime/seoboot-requests"))
    out=Path(os.environ.get("CEREBRO_SEOBOOT_RESULT_ROOT",".cerebro-runtime/seoboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_seo(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
