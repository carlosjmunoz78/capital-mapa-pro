from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="KBOOT-001"
ALLOWED_ENGINES={"BMD-001","PROC-001","WAUD-001","KW-001","SOCAUD-001","LOCALP-001","COMPET-001"}

def bootstrap_company_knowledge(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    inputs=payload.get("inputs") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(inputs,list): raise ValueError("inputs must be list")
    records=[]
    for item in inputs:
        if not isinstance(item,dict): raise ValueError("knowledge input must be object")
        if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company knowledge input denied")
        engine_id=str(item.get("engine_id",""))
        if engine_id not in ALLOWED_ENGINES: raise ValueError("unsupported bootstrap source engine")
        evidence_ref=str(item.get("evidence_hash") or item.get("source_evidence_hash") or "").strip()
        if not evidence_ref: raise ValueError("provenance required for knowledge bootstrap")
        canonical=json.dumps(item,sort_keys=True,separators=(",",":"))
        records.append({
          "knowledge_id":"kb-"+hashlib.sha256((company_id+"|"+engine_id+"|"+canonical).encode()).hexdigest()[:24],
          "source_engine_id":engine_id,"source_evidence_ref":evidence_ref,
          "source_status":str(item.get("status","")),"confidence":float(item.get("confidence",0.0) or 0.0),
          "content_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
          "promotion_status":"CANDIDATE",
        })
    records=sorted(records,key=lambda x:(x["source_engine_id"],x["knowledge_id"]))
    canonical=json.dumps({"company_id":company_id,"records":records},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_knowledge_bootstrap","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":"LAB","version":str(payload.get("version","1.0.0")),
      "knowledge_candidates":records,"candidate_count":len(records),
      "status":"GREEN" if records else "WAITING",
      "required_downstream_gates":["PRV-001","KNW-001","RAG-001"],
      "direct_knowledge_promotion_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_KBOOT_REQUEST_ROOT",".cerebro-runtime/kboot-requests"))
    out=Path(os.environ.get("CEREBRO_KBOOT_RESULT_ROOT",".cerebro-runtime/kboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_company_knowledge(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'; target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
