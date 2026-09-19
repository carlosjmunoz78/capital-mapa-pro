from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ENGINE_ID="PROC-001"
REQUIRED=("name","inputs","outputs")
OPTIONAL=("owner","dependencies","systems","documents","blockers","trigger","frequency")

def _list(v):
    if v is None:return []
    if isinstance(v,list):return [str(x).strip() for x in v if str(x).strip()]
    s=str(v).strip()
    return [s] if s else []

def _normalize(candidate:dict,index:int)->dict:
    if not isinstance(candidate,dict): raise ValueError("process candidate must be object")
    name=str(candidate.get("name","")).strip()
    inputs=_list(candidate.get("inputs"))
    outputs=_list(candidate.get("outputs"))
    if not name or not inputs or not outputs:
        raise ValueError("process candidate requires name, inputs and outputs")
    base={
        "process_id":str(candidate.get("process_id") or f"PROC-CAND-{index:03d}"),
        "name":name,
        "inputs":inputs,
        "outputs":outputs,
        "owner":str(candidate.get("owner","")).strip(),
        "dependencies":_list(candidate.get("dependencies")),
        "systems":_list(candidate.get("systems")),
        "documents":_list(candidate.get("documents")),
        "blockers":_list(candidate.get("blockers")),
        "trigger":str(candidate.get("trigger","")).strip(),
        "frequency":str(candidate.get("frequency","")).strip(),
        "evidence_refs":sorted(set(_list(candidate.get("evidence_refs")))),
    }
    completeness=sum(bool(base.get(k)) for k in ("name","inputs","outputs","owner","evidence_refs"))/5
    base["confidence"]=round(0.45+0.55*completeness,3)
    base["missing_fields"]=[k for k in ("owner","evidence_refs") if not base.get(k)]
    return base

def discover_processes(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    candidates=payload.get("process_candidates") or []
    if not isinstance(candidates,list): raise ValueError("process_candidates must be list")
    normalized=[_normalize(x,i+1) for i,x in enumerate(candidates)]
    normalized=sorted(normalized,key=lambda x:(x["name"].lower(),x["process_id"]))
    avg=round(sum(x["confidence"] for x in normalized)/len(normalized),3) if normalized else 0.0
    unresolved=sum(1 for x in normalized if x["missing_fields"])
    canonical=json.dumps({"company_id":company_id,"processes":normalized},sort_keys=True,separators=(",",":"))
    return {
        "record_type":"process_discovery",
        "company_id":company_id,
        "engine_id":ENGINE_ID,
        "environment":str(payload.get("environment","LAB")).upper(),
        "version":str(payload.get("version","1.0.0")),
        "processes":normalized,
        "process_count":len(normalized),
        "unresolved_process_count":unresolved,
        "confidence":avg,
        "status":"GREEN" if normalized and unresolved==0 else "PARTIAL" if normalized else "WAITING",
        "external_mutation_allowed":False,
        "candidate_only":True,
        "cost_eur":0.0,
        "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_PROC_REQUEST_ROOT",".cerebro-runtime/process-discovery-requests"))
    out=Path(os.environ.get("CEREBRO_PROC_RESULT_ROOT",".cerebro-runtime/process-discovery-results"))
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        result=discover_processes(payload)
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
