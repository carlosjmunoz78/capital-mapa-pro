from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

def rebuild_company(company_id:str,environment:str)->dict:
    if environment=="PROD":
        return {
            "company_id":company_id,
            "engine_id":"RBLD-001",
            "status":"HUMAN_REQUIRED",
            "human_reason":"HIGH_RISK",
            "rebuild_performed":False,
            "external_mutation_allowed":False,
        }
    from jobs.permissioned_rag_cache import build_index
    from jobs.build_digital_twin_snapshot import run as build_twin
    rag_written=build_index()
    twin_written=build_twin()
    rag_root=Path(os.environ.get("CEREBRO_RAG_INDEX_ROOT",".cerebro-runtime/rag-index"))
    twin_root=Path(os.environ.get("CEREBRO_DIGITAL_TWIN_ROOT",".cerebro-runtime/digital-twin"))
    rag_ok=(rag_root/f"{company_id}.json").exists()
    twin_ok=(twin_root/f"{company_id}.snapshot.json").exists()
    return {
        "company_id":company_id,
        "engine_id":"RBLD-001",
        "environment":environment,
        "status":"GREEN" if rag_ok and twin_ok else "BLOCKED",
        "rebuild_performed":True,
        "rebuild_scope":["RAG-001","TWIN-001"],
        "postcheck":{"rag_index":rag_ok,"digital_twin":twin_ok},
        "written":[str(p) for p in [*rag_written,*twin_written]],
        "prod_write_performed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    out_root=Path(os.environ.get("CEREBRO_REBUILD_RESULT_ROOT",".cerebro-runtime/rebuild-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        result=rebuild_company(str(cfg["company_id"]),str(cfg["environment"]).upper())
        target=out_root/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
