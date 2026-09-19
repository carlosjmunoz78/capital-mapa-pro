from __future__ import annotations

import json
import os
from pathlib import Path

TERMINAL_OK={"GREEN","PASS","PASSED","OK"}
TERMINAL_BAD={"RED","FAIL","FAILED","BLOCKED","HUMAN_REQUIRED"}

def compare_case(case:dict)->dict:
    case_id=str(case.get("case_id","")).strip()
    if not case_id:
        raise ValueError("case_id required")
    expected=case.get("expected")
    actual=case.get("actual")
    equal=expected==actual
    return {
        "case_id":case_id,
        "expected":expected,
        "actual":actual,
        "status":"GREEN" if equal else "REGRESSION",
        "regression":not equal,
    }

def run()->list[Path]:
    source_root=Path(os.environ.get("CEREBRO_GOLDEN_SUITE_ROOT",".cerebro-runtime/golden-suites"))
    out_root=Path(os.environ.get("CEREBRO_REGRESSION_ROOT",".cerebro-runtime/regression"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("golden suite must be object")
        company_id=str(payload.get("company_id","")).strip()
        engine_id=str(payload.get("engine_id","")).strip()
        environment=str(payload.get("environment","LAB")).strip().upper()
        version=str(payload.get("version","1.0.0")).strip()
        if not all((company_id,engine_id,environment,version)):
            raise ValueError("complete regression scope required")
        if environment=="PROD":
            raise ValueError("REG-001 replay must run before PROD, not in PROD")
        cases=payload.get("cases")
        if not isinstance(cases,list) or not cases:
            raise ValueError("golden cases required")
        results=[compare_case(case) for case in cases]
        regressions=sum(1 for r in results if r["regression"])
        target=out_root/f"{company_id}.{engine_id}.json"
        target.write_text(json.dumps({
            "record_type":"regression_suite_result",
            "company_id":company_id,
            "engine_id":"REG-001",
            "target_engine_id":engine_id,
            "environment":environment,
            "version":version,
            "golden_suite_version":str(payload.get("golden_suite_version","")),
            "cases":results,
            "case_count":len(results),
            "regression_count":regressions,
            "status":"GREEN" if regressions==0 else "BLOCKED",
            "promotion_allowed":False,
            "external_mutation_allowed":False,
            "production_ready":False,
            "cost_eur":0.0,
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
