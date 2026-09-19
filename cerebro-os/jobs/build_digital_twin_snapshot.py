from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ALLOWED_SOURCE_KINDS={"KNOWLEDGE_INVENTORY","LEARNING_OUTCOME","META_LEARNING","FINOPS","SIMULATION_RESULT"}

def _hash_payload(payload:object)->str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _load_company_json(path:Path,company_id:str)->object:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload,dict):
        cid=str(payload.get("company_id","")).strip()
        if cid and cid!=company_id: raise ValueError("cross-company twin source denied")
    elif isinstance(payload,list):
        for item in payload:
            if isinstance(item,dict):
                cid=str(item.get("company_id","")).strip()
                if cid and cid!=company_id: raise ValueError("cross-company twin source denied")
    else:
        raise ValueError("unsupported twin source payload")
    return payload

def build_snapshot(company_id:str,environment:str,version:str)->dict:
    if not all((company_id.strip(),environment.strip(),version.strip())):
        raise ValueError("complete twin scope required")
    if environment=="PROD":
        raise ValueError("TWIN-001 snapshot runtime must not target PROD")

    roots={
      "KNOWLEDGE_INVENTORY":Path(os.environ.get("CEREBRO_KNOWLEDGE_INVENTORY_ROOT",".cerebro-runtime/knowledge-inventory")),
      "LEARNING_OUTCOME":Path(os.environ.get("CEREBRO_LEARNING_OUTCOME_ROOT",".cerebro-runtime/learning-outcomes")),
      "META_LEARNING":Path(os.environ.get("CEREBRO_META_LEARNING_ROOT",".cerebro-runtime/meta-learning")),
      "FINOPS":Path(os.environ.get("CEREBRO_FINOPS_ROOT",".cerebro-runtime/finops")),
      "SIMULATION_RESULT":Path(os.environ.get("CEREBRO_SIMULATION_RESULT_ROOT",".cerebro-runtime/simulation-results")),
    }
    sources=[]
    for kind,root in roots.items():
        candidates=[]
        if kind=="KNOWLEDGE_INVENTORY":
            candidates=[root/f"{company_id}.json"]
        elif kind in {"LEARNING_OUTCOME","META_LEARNING","FINOPS"}:
            candidates=[root/f"{company_id}.json"]
        else:
            candidates=sorted(root.glob(f"{company_id}.*.json"))
        for path in candidates:
            if not path.exists(): continue
            payload=_load_company_json(path,company_id)
            sources.append({
              "kind":kind,
              "path":str(path),
              "payload_hash":_hash_payload(payload),
              "payload":payload,
            })

    snapshot_core={
      "company_id":company_id,
      "engine_id":"TWIN-001",
      "environment":environment,
      "version":version,
      "source_count":len(sources),
      "sources":sources,
      "synthetic_overlay_only":True,
      "writes_to_prod":False,
      "external_mutation_allowed":False,
      "live_traffic_exposed":False,
      "production_ready":False,
      "cost_eur":0.0,
    }
    snapshot_id="twin-"+_hash_payload(snapshot_core)[:24]
    return {**snapshot_core,"snapshot_id":snapshot_id,"record_type":"digital_twin_snapshot"}

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    out_root=Path(os.environ.get("CEREBRO_DIGITAL_TWIN_ROOT",".cerebro-runtime/digital-twin"))
    out_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        company_id=str(cfg["company_id"]); environment=str(cfg["environment"]); version=str(cfg["version"])
        snapshot=build_snapshot(company_id,environment,version)
        target=out_root/f"{company_id}.snapshot.json"
        target.write_text(json.dumps(snapshot,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for path in run(): print(path)
