from __future__ import annotations

REMOTE_SAFE_PHASES={
    "REGISTER_COMPANY","SCAN_DIGITAL_FOOTPRINT","DISCOVER_BUSINESS_MODEL","DISCOVER_PROCESSES",
    "AUDIT_WEBSITE","DISCOVER_KEYWORDS","AUDIT_SOCIAL_MEDIA","AUDIT_LOCAL_PRESENCE",
    "MAP_COMPETITORS","BOOTSTRAP_COMPANY_KNOWLEDGE","BUILD_SEO_PLAN","BUILD_SOCIAL_PLAN",
    "BUILD_MARKETING_PLAN","DETERMINE_REQUIRED_ENGINES",
}
LOCAL_ACCESS_PHASES={"MINIMUM_ACCESSES"}
PREPROD_SAFE_PHASES={
    "BOOTSTRAP_CRM","BOOTSTRAP_APP","BOOTSTRAP_AUTOMATIONS","BOOTSTRAP_TRAINING",
    "CREATE_SUPERVISOR_SCOPE","CREATE_BACKUP_REBUILD_PACK","PREPROD_TESTS",
}
PROD_PHASES={"PRODUCTION_ACTIVATION"}

def assess_remote_onboarding_gaps(result:dict)->dict:
    if not isinstance(result,dict):
        raise ValueError("onboarding result must be object")
    company_id=str(result.get("company_id","")).strip()
    version=str(result.get("version","1.0.0")).strip()
    if not company_id or not version:
        raise ValueError("company_id/version required")

    status=str(result.get("status","UNKNOWN")).upper()
    state=result.get("state") or {}
    if not isinstance(state,dict):
        raise ValueError("state must be object")
    if str(state.get("company_id",company_id))!=company_id:
        raise ValueError("cross-company onboarding state denied")

    phase=str(state.get("current_phase") or "").strip()
    human_reason=str(result.get("human_reason") or state.get("human_reason") or "").strip() or None
    stop_reason=str(result.get("executor_stop_reason") or result.get("stop_reason") or "").strip() or None

    if status=="HUMAN_REQUIRED":
        classification="HUMAN_REQUIRED"
        remotely_actionable=False
        local_pc_required=False
    elif phase in REMOTE_SAFE_PHASES:
        classification="REMOTE_SAFE"
        remotely_actionable=True
        local_pc_required=False
    elif phase in PREPROD_SAFE_PHASES:
        classification="REMOTE_PREPROD_SAFE"
        remotely_actionable=True
        local_pc_required=False
    elif phase in LOCAL_ACCESS_PHASES:
        classification="LOCAL_ACCESS_DEPENDENT"
        remotely_actionable=False
        local_pc_required=True
    elif phase in PROD_PHASES:
        classification="PROD_GATE"
        remotely_actionable=False
        local_pc_required=False
    elif not phase and status=="GREEN":
        classification="COMPLETE"
        remotely_actionable=False
        local_pc_required=False
    else:
        classification="UNKNOWN_GAP"
        remotely_actionable=False
        local_pc_required=False

    prefill=result.get("remote_prefill") or {}
    green_prefill=int(prefill.get("green_engine_count",0) or 0)
    engine_count=int(prefill.get("engine_count",0) or 0)
    remaining=max(0,engine_count-green_prefill)

    next_action={
        "REMOTE_SAFE":"RUN_OR_RESUME_REMOTE_SAFE_PHASE",
        "REMOTE_PREPROD_SAFE":"RUN_OR_RESUME_PREPROD_PHASE",
        "LOCAL_ACCESS_DEPENDENT":"WAIT_FOR_LOCAL_ACCESS_OR_EXISTING_CLOUD_EVIDENCE",
        "HUMAN_REQUIRED":"WAIT_FOR_CANONICAL_HUMAN_EXCEPTION",
        "PROD_GATE":"KEEP_PROD_FAIL_CLOSED",
        "COMPLETE":"NO_ACTION",
        "UNKNOWN_GAP":"AUDIT_GAP_BEFORE_RETRY",
    }[classification]

    return {
      "record_type":"remote_onboarding_gap_assessment",
      "company_id":company_id,
      "engine_id":"ONB-GAP-001",
      "environment":str(state.get("environment") or result.get("environment") or "LAB"),
      "version":version,
      "status":"GREEN" if classification in {"REMOTE_SAFE","REMOTE_PREPROD_SAFE","COMPLETE"} else "WAITING" if classification in {"LOCAL_ACCESS_DEPENDENT","PROD_GATE","UNKNOWN_GAP"} else "HUMAN_REQUIRED",
      "classification":classification,
      "current_phase":phase or None,
      "source_status":status,
      "stop_reason":stop_reason,
      "human_reason":human_reason,
      "remotely_actionable":remotely_actionable,
      "local_pc_required":local_pc_required,
      "remote_prefill_green_count":green_prefill,
      "remote_prefill_total":engine_count,
      "remote_prefill_remaining":remaining,
      "next_action":next_action,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }

def assess_many(results:list[dict])->dict:
    rows=[assess_remote_onboarding_gaps(x) for x in results]
    return {
      "record_type":"remote_onboarding_gap_batch",
      "engine_id":"ONB-GAP-001",
      "status":"HUMAN_REQUIRED" if any(x["status"]=="HUMAN_REQUIRED" for x in rows) else "GREEN",
      "companies":tuple(rows),
      "remote_actionable_count":sum(1 for x in rows if x["remotely_actionable"]),
      "local_pc_required_count":sum(1 for x in rows if x["local_pc_required"]),
      "human_required_count":sum(1 for x in rows if x["status"]=="HUMAN_REQUIRED"),
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }
