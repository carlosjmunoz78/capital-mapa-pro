from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="TRNBOOT-001"

def bootstrap_training(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    sources=payload.get("knowledge_sources") or []
    evals=payload.get("evaluation_cases") or []
    if not isinstance(sources,list) or not isinstance(evals,list): raise ValueError("knowledge_sources and evaluation_cases must be lists")
    refs=sorted({str(x).strip() for x in sources if str(x).strip()})
    cases=[]
    for i,item in enumerate(evals,1):
        if not isinstance(item,dict): raise ValueError("evaluation case must be object")
        prompt=str(item.get("input","")).strip(); expected=str(item.get("expected","")).strip()
        if prompt and expected: cases.append({"case_id":str(item.get("case_id") or f"EVAL-{i:03d}"),"input":prompt,"expected":expected})
    canonical=json.dumps({"company_id":company_id,"sources":refs,"cases":cases},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"training_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"LAB","version":str(payload.get("version","1.0.0")),
      "status":"GREEN" if refs and cases else "PARTIAL" if refs or cases else "WAITING","knowledge_sources":refs,"evaluation_cases":cases,
      "train_on_prod_data_allowed":False,"direct_prod_promotion_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["PRV-001","EVA-001","JDG-001","REG-001"],"evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_TRNBOOT_REQUEST_ROOT",".cerebro-runtime/trnboot-requests"))
    out=Path(os.environ.get("CEREBRO_TRNBOOT_RESULT_ROOT",".cerebro-runtime/trnboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_training(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
