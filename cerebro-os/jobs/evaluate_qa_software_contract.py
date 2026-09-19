from __future__ import annotations

import json
import os
from pathlib import Path

REQUIRED_LAYERS=("unit","contract","integration","e2e","security","regression")

def evaluate_manifest(payload:dict)->dict:
    engine_id=str(payload.get("engine_id","")).strip()
    company_id=str(payload.get("company_id","GLOBAL")).strip()
    environment=str(payload.get("environment","LAB")).strip().upper()
    version=str(payload.get("version","1.0.0")).strip()
    layers=payload.get("layers")
    if not all((engine_id,company_id,environment,version)) or not isinstance(layers,dict):
        raise ValueError("complete QA manifest required")
    results={}
    missing=[]
    failed=[]
    for layer in REQUIRED_LAYERS:
        item=layers.get(layer)
        if not isinstance(item,dict):
            missing.append(layer); continue
        status=str(item.get("status","")).upper()
        if status!="GREEN":
            failed.append(layer)
        results[layer]={
            "status":status or "MISSING",
            "evidence_ref":str(item.get("evidence_ref","")),
        }
        if status=="GREEN" and not results[layer]["evidence_ref"]:
            failed.append(layer)
    status="GREEN" if not missing and not failed else "BLOCKED"
    return {
        "record_type":"qa_software_contract_result",
        "company_id":company_id,
        "engine_id":"QA-001",
        "target_engine_id":engine_id,
        "environment":environment,
        "version":version,
        "required_layers":list(REQUIRED_LAYERS),
        "layers":results,
        "missing_layers":sorted(set(missing)),
        "failed_layers":sorted(set(failed)),
        "status":status,
        "promotion_allowed":False,
        "external_mutation_allowed":False,
        "production_ready":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    source_root=Path(os.environ.get("CEREBRO_QA_MANIFEST_ROOT",".cerebro-runtime/qa-manifests"))
    out_root=Path(os.environ.get("CEREBRO_QA_RESULT_ROOT",".cerebro-runtime/qa-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("QA manifest must be object")
        result=evaluate_manifest(payload)
        target=out_root/f'{result["company_id"]}.{result["target_engine_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
