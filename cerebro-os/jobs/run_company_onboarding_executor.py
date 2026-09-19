from __future__ import annotations

import json
import os
from pathlib import Path

from jobs.company_onboarding_orchestrator import initial_state
from jobs.company_onboarding_executor import execute_onboarding_superloop
from jobs.company_onboarding_default_handlers import build_default_onboarding_registry

def run_request(payload:dict,previous:dict|None=None)->dict:
    if not isinstance(payload,dict):
        raise ValueError("onboarding request must be object")
    company_id=str(payload.get("company_id","")).strip()
    if not company_id:
        raise ValueError("company_id required")
    version=str(payload.get("version","1.0.0")).strip()
    if not version:
        raise ValueError("version required")
    context=payload.get("context") or {}
    if not isinstance(context,dict):
        raise ValueError("context must be object")

    if previous:
        if str(previous.get("company_id",""))!=company_id:
            raise ValueError("cross-company previous onboarding state denied")
        state=dict(previous.get("state") or initial_state(company_id,version))
        previous_results=previous.get("engine_results") or []
        if not isinstance(previous_results,list):
            raise ValueError("previous engine_results must be list")
        persisted={}
        for row in previous_results:
            if not isinstance(row,dict):
                raise ValueError("previous engine result must be object")
            if str(row.get("company_id",""))!=company_id:
                raise ValueError("cross-company persisted engine result denied")
            eid=str(row.get("engine_id","")).strip()
            if eid:
                persisted[eid]=dict(row)
        supplied=context.get("engine_results") or {}
        if supplied and not isinstance(supplied,dict):
            raise ValueError("context.engine_results must be object")
        merged={**persisted,**(supplied if isinstance(supplied,dict) else {})}
        context={**context,"engine_results":merged}
    else:
        state=initial_state(company_id,version)

    result=execute_onboarding_superloop(
        state,
        registry=build_default_onboarding_registry(),
        context=context,
        max_steps=int(payload.get("max_steps",50)),
    )
    return {
      **result,
      "record_type":"company_onboarding_executor_run",
      "runner_version":"v0",
      "company_id":company_id,
      "version":version,
      "automatic_resume_supported":True,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }

def run()->list[Path]:
    request_root=Path(os.environ.get("CEREBRO_ONBOARD_EXEC_REQUEST_ROOT",".cerebro-runtime/onboarding-executor-requests"))
    result_root=Path(os.environ.get("CEREBRO_ONBOARD_EXEC_RESULT_ROOT",".cerebro-runtime/onboarding-executor-results"))
    result_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(request_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        company_id=str(payload.get("company_id","")).strip()
        if not company_id:
            raise ValueError("company_id required")
        target=result_root/f"{company_id}.json"
        previous=json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
        result=run_request(payload,previous)
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for path in run():
        print(path)
