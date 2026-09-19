from __future__ import annotations

from jobs.company_onboarding_default_handlers import build_default_onboarding_registry

REMOTE_PREFILL_PLAN=(
    ("COMP-REG-001","LOCAL_DETERMINISTIC",()),
    ("SCAN-001","READ_ONLY",()),
    ("BMD-001","READ_ONLY",()),
    ("PROC-001","READ_ONLY",()),
    ("KW-001","READ_ONLY",()),
    ("SOCAUD-001","READ_ONLY",()),
    ("LOCALP-001","READ_ONLY",()),
    ("COMPET-001","READ_ONLY",()),
    ("WAUD-001","READ_ONLY",("SCAN-001",)),
    ("KBOOT-001","LOCAL_DETERMINISTIC",("BMD-001","PROC-001","WAUD-001","KW-001","SOCAUD-001","LOCALP-001","COMPET-001")),
    ("SEOBOOT-001","LOCAL_DETERMINISTIC",("WAUD-001","KW-001")),
    ("SOCBOOT-001","LOCAL_DETERMINISTIC",("SOCAUD-001","BMD-001")),
    ("MKTBOOT-001","LOCAL_DETERMINISTIC",("BMD-001","KW-001")),
)

def prefill_remote_safe_context(*,company_id:str,version:str,context:dict)->dict:
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id/version required")
    if not isinstance(context,dict):
        raise ValueError("context must be object")

    seeded=context.get("engine_results") or {}
    if not isinstance(seeded,dict):
        raise ValueError("context.engine_results must be object")
    results={str(k):dict(v) for k,v in seeded.items() if isinstance(v,dict)}
    for eid,row in results.items():
        if str(row.get("company_id","")) not in {"",company_id}:
            raise ValueError("cross-company prefill evidence denied")
        if row.get("company_id") in {None,""}:
            row["company_id"]=company_id

    reg=build_default_onboarding_registry()
    events=[]
    for engine_id,mode,deps in REMOTE_PREFILL_PLAN:
        cached=results.get(engine_id)
        if cached and str(cached.get("status","")).upper()=="GREEN":
            events.append({
              "engine_id":engine_id,"status":"SKIPPED_GREEN","result_source":"PERSISTED_GREEN",
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue
        missing=[dep for dep in deps if dep not in results]
        if missing:
            events.append({
              "engine_id":engine_id,"status":"WAITING_DEPENDENCY","missing_dependencies":tuple(missing),
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue
        handler=reg.get(engine_id)
        if handler is None:
            events.append({
              "engine_id":engine_id,"status":"HANDLER_MISSING",
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue
        if mode not in handler.execution_modes:
            events.append({
              "engine_id":engine_id,"status":"MODE_MISMATCH","required_mode":mode,
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue

        payload={
          "company_id":company_id,"engine_id":engine_id,"phase":"REMOTE_PREFILL",
          "environment":"LAB","version":version,"execution_mode":mode,
          "allowed_external_mutation":False,"required_cost_eur":0.0,
          "required_gates":(),"context":{**context,"engine_results":results},
        }
        try:
            result=handler.handler(payload)
        except Exception as exc:
            events.append({
              "engine_id":engine_id,"status":"BLOCKED_EXCEPTION","error_type":type(exc).__name__,
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue
        if not isinstance(result,dict):
            events.append({
              "engine_id":engine_id,"status":"BLOCKED_INVALID_RESULT",
              "remote_safe":True,"external_mutation_allowed":False,"cost_eur":0.0,
            })
            continue
        if str(result.get("company_id",""))!=company_id:
            raise ValueError("cross-company prefill result denied")
        if str(result.get("engine_id",""))!=engine_id:
            raise ValueError("prefill engine_id mismatch")
        if result.get("external_mutation_performed"):
            raise ValueError("remote prefill reported forbidden external mutation")
        if float(result.get("cost_eur",0.0))!=0.0:
            raise ValueError("remote prefill reported non-zero cost")

        results[engine_id]=dict(result)
        events.append({
          "engine_id":engine_id,"status":str(result.get("status","UNKNOWN")).upper(),
          "evidence_ref":str(result.get("evidence_hash") or result.get("evidence_ref") or ""),
          "result_source":"REMOTE_PREFILL_EXECUTED","remote_safe":True,
          "external_mutation_allowed":False,"cost_eur":0.0,
        })

    green=sum(1 for row in results.values() if str(row.get("status","")).upper()=="GREEN")
    return {
      "context":{**context,"engine_results":results},
      "events":tuple(events),
      "remote_prefill_engine_count":len(REMOTE_PREFILL_PLAN),
      "green_engine_count":green,
      "local_browser_required":False,
      "computer_use_performed":False,
      "external_mutation_allowed":False,
      "cost_eur":0.0,
    }
