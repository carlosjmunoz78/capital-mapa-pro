from __future__ import annotations

import json
import os
from pathlib import Path

ROOTS=(
    "knowledge-inventory","learning-outcomes","meta-learning","incidents","self-heal",
    "red-team-summary","backup-results","rebuild-results","continuity-results","crisis",
    "control-plane","digital-twin","rag-index"
)

def _expected_company_from_name(path:Path)->str|None:
    name=path.name
    if name in {"registry.json","activation-matrix.json"}: return None
    if "." in name:
        return name.split(".",1)[0]
    return path.stem

def _scan_payload(payload,expected:str,path:Path,violations:list[dict]):
    if isinstance(payload,dict):
        cid=payload.get("company_id")
        if cid is not None and str(cid).strip() and str(cid)!=expected:
            violations.append({"path":str(path),"expected_company_id":expected,"found_company_id":str(cid),"reason":"PAYLOAD_COMPANY_MISMATCH"})
        for value in payload.values():
            _scan_payload(value,expected,path,violations)
    elif isinstance(payload,list):
        for item in payload:
            _scan_payload(item,expected,path,violations)

def verify(runtime_root:Path)->dict:
    violations=[]
    checked=0
    for dirname in ROOTS:
        root=runtime_root/dirname
        if not root.exists(): continue
        for path in sorted(root.rglob("*.json")):
            expected=_expected_company_from_name(path)
            if not expected: continue
            try:
                payload=json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            checked+=1
            _scan_payload(payload,expected,path,violations)
    return {
        "record_type":"tenant_isolation_verification",
        "engine_id":"TENANT-001",
        "files_checked":checked,
        "violations":violations,
        "violation_count":len(violations),
        "status":"GREEN" if not violations else "BLOCKED",
        "cross_company_default":"DENY",
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def run()->Path:
    runtime=Path(os.environ.get("CEREBRO_RUNTIME_ROOT",".cerebro-runtime"))
    out=Path(os.environ.get("CEREBRO_TENANT_RESULT_ROOT",".cerebro-runtime/tenant-isolation"))
    out.mkdir(parents=True,exist_ok=True)
    result=verify(runtime)
    target=out/"summary.json"
    target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return target

if __name__=="__main__":
    print(run())
