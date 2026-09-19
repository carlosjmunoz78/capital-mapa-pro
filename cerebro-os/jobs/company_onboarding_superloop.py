from __future__ import annotations
import json,os
from pathlib import Path

from jobs.company_onboarding_orchestrator import advance,default_phase_plan,PHASE_ENGINE_MAP

NON_ADVANCING_STATUSES={"WAITING","PARTIAL","DEGRADED","UNKNOWN","PENDING","IN_PROGRESS"}
BLOCKING_STATUSES={"BLOCKED","RED","FAILED"}
VALID_HUMAN_REASONS={
    "LEGAL_REQUIRED","SIGNATURE_REQUIRED","LOW_CONFIDENCE","HIGH_RISK",
    "POLICY_CONFLICT","SECURITY_INCIDENT","MONEY_LIMIT","CUSTOMER_HUMAN_REQUEST",
}

def _index_results(company_id:str,engine_results:list[dict])->dict[str,dict]:
    indexed={}
    for row in engine_results:
        if not isinstance(row,dict):
            raise ValueError("engine result must be object")
        if str(row.get("company_id",""))!=company_id:
            raise ValueError("cross-company engine result denied")
        engine_id=str(row.get("engine_id","")).strip()
        if not engine_id:
            raise ValueError("engine_id required in result")
        indexed[engine_id]=row
    return indexed

def _phase_result(*,company_id:str,phase:str,row:dict)->dict:
    status=str(row.get("status","UNKNOWN")).upper()
    evidence_ref=str(row.get("evidence_hash") or row.get("evidence_ref") or "").strip()
    if status=="GREEN":
        return {"company_id":company_id,"phase":phase,"status":"GREEN","evidence_ref":evidence_ref}
    if status=="HUMAN_REQUIRED":
        reason=str(row.get("human_reason") or row.get("reason") or "LOW_CONFIDENCE")
        if reason not in VALID_HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")
        return {
            "company_id":company_id,"phase":phase,"status":"HUMAN_REQUIRED",
            "evidence_ref":evidence_ref,"human_reason":reason,"reason":reason,
        }
    if status in BLOCKING_STATUSES:
        return {
            "company_id":company_id,"phase":phase,"status":"BLOCKED",
            "evidence_ref":evidence_ref,"reason":str(row.get("reason") or status),
        }
    if status in NON_ADVANCING_STATUSES:
        return {
            "company_id":company_id,"phase":phase,"status":"WAITING",
            "evidence_ref":evidence_ref,"reason":str(row.get("reason") or status),
        }
    raise ValueError(f"unsupported engine result status: {status}")

def run_superloop(state:dict,engine_results:list[dict],max_steps:int=50)->dict:
    company_id=str(state.get("company_id","")).strip()
    if not company_id:
        raise ValueError("company_id required")
    if max_steps<1:
        raise ValueError("max_steps must be >= 1")
    indexed=_index_results(company_id,engine_results)
    current=dict(state)
    processed=[]
    seen_phases=set()

    for _ in range(max_steps):
        phase=current.get("current_phase")
        if phase is None:
            return {
                "company_id":company_id,"status":"GREEN","state":current,
                "processed_steps":tuple(processed),"next_execution_plan":None,
                "stop_reason":"ONBOARDING_COMPLETE","external_mutation_allowed":False,"cost_eur":0.0,
            }
        phase=str(phase)
        if phase in seen_phases:
            raise ValueError("superloop phase cycle detected")
        seen_phases.add(phase)
        target_engine=PHASE_ENGINE_MAP.get(phase)
        if not target_engine:
            raise ValueError("phase engine binding missing")

        row=indexed.get(target_engine)
        if row is None:
            return {
                "company_id":company_id,"status":"WAITING","state":current,
                "processed_steps":tuple(processed),"next_execution_plan":default_phase_plan(current),
                "stop_reason":"ENGINE_RESULT_MISSING","missing_engine_id":target_engine,
                "external_mutation_allowed":False,"cost_eur":0.0,
            }

        phase_result=_phase_result(company_id=company_id,phase=phase,row=row)
        current=advance(current,phase_result)
        processed.append({
            "phase":phase,"engine_id":target_engine,
            "input_status":str(row.get("status","UNKNOWN")).upper(),
            "phase_status":phase_result["status"],
            "evidence_ref":phase_result.get("evidence_ref",""),
        })

        if current.get("status")=="HUMAN_REQUIRED":
            return {
                "company_id":company_id,"status":"HUMAN_REQUIRED","state":current,
                "processed_steps":tuple(processed),"next_execution_plan":None,
                "stop_reason":"HUMAN_REQUIRED","human_reason":current.get("human_reason"),
                "external_mutation_allowed":False,"cost_eur":0.0,
            }
        if phase_result["status"]=="BLOCKED":
            return {
                "company_id":company_id,"status":"BLOCKED","state":current,
                "processed_steps":tuple(processed),"next_execution_plan":default_phase_plan(current),
                "stop_reason":"ENGINE_BLOCKED","blocked_engine_id":target_engine,
                "external_mutation_allowed":False,"cost_eur":0.0,
            }
        if phase_result["status"]=="WAITING":
            return {
                "company_id":company_id,"status":"WAITING","state":current,
                "processed_steps":tuple(processed),"next_execution_plan":default_phase_plan(current),
                "stop_reason":"ENGINE_NOT_GREEN","waiting_engine_id":target_engine,
                "external_mutation_allowed":False,"cost_eur":0.0,
            }

    return {
        "company_id":company_id,"status":"BLOCKED","state":current,
        "processed_steps":tuple(processed),"next_execution_plan":default_phase_plan(current),
        "stop_reason":"MAX_STEPS_REACHED","external_mutation_allowed":False,"cost_eur":0.0,
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_ONBOARD_SUPERLOOP_REQUEST_ROOT",".cerebro-runtime/onboarding-superloop-requests"))
    out=Path(os.environ.get("CEREBRO_ONBOARD_SUPERLOOP_RESULT_ROOT",".cerebro-runtime/onboarding-superloop-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        result=run_superloop(
            dict(payload.get("state") or {}),
            list(payload.get("engine_results") or []),
            int(payload.get("max_steps",50)),
        )
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
