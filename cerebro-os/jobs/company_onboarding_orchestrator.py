from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

PHASES=(
    "REGISTER_COMPANY",
    "MINIMUM_ACCESSES",
    "SCAN_DIGITAL_FOOTPRINT",
    "DISCOVER_BUSINESS_MODEL",
    "DISCOVER_PROCESSES",
    "AUDIT_WEBSITE",
    "DISCOVER_KEYWORDS",
    "AUDIT_SOCIAL_MEDIA",
    "AUDIT_LOCAL_PRESENCE",
    "MAP_COMPETITORS",
    "BOOTSTRAP_COMPANY_KNOWLEDGE",
    "BUILD_SEO_PLAN",
    "BUILD_SOCIAL_PLAN",
    "BUILD_MARKETING_PLAN",
    "DETERMINE_REQUIRED_ENGINES",
    "BOOTSTRAP_CRM",
    "BOOTSTRAP_APP",
    "BOOTSTRAP_AUTOMATIONS",
    "BOOTSTRAP_TRAINING",
    "CREATE_SUPERVISOR_SCOPE",
    "CREATE_BACKUP_REBUILD_PACK",
    "PREPROD_TESTS",
    "PRODUCTION_ACTIVATION",
)
READ_ONLY_DISCOVERY={
    "SCAN_DIGITAL_FOOTPRINT","DISCOVER_BUSINESS_MODEL","DISCOVER_PROCESSES",
    "AUDIT_WEBSITE","DISCOVER_KEYWORDS","AUDIT_SOCIAL_MEDIA","AUDIT_LOCAL_PRESENCE",
    "MAP_COMPETITORS"
}
PREPROD_ONLY={
    "BOOTSTRAP_CRM","BOOTSTRAP_APP","BOOTSTRAP_AUTOMATIONS","BOOTSTRAP_TRAINING",
    "CREATE_SUPERVISOR_SCOPE","CREATE_BACKUP_REBUILD_PACK","PREPROD_TESTS"
}
PHASE_ENGINE_MAP={
    "REGISTER_COMPANY":"COMP-REG-001",
    "MINIMUM_ACCESSES":"ACCESSBOOT-001",
    "SCAN_DIGITAL_FOOTPRINT":"SCAN-001",
    "DISCOVER_BUSINESS_MODEL":"BMD-001",
    "DISCOVER_PROCESSES":"PROC-001",
    "AUDIT_WEBSITE":"WAUD-001",
    "DISCOVER_KEYWORDS":"KW-001",
    "AUDIT_SOCIAL_MEDIA":"SOCAUD-001",
    "AUDIT_LOCAL_PRESENCE":"LOCALP-001",
    "MAP_COMPETITORS":"COMPET-001",
    "BOOTSTRAP_COMPANY_KNOWLEDGE":"KBOOT-001",
    "BUILD_SEO_PLAN":"SEOBOOT-001",
    "BUILD_SOCIAL_PLAN":"SOCBOOT-001",
    "BUILD_MARKETING_PLAN":"MKTBOOT-001",
    "DETERMINE_REQUIRED_ENGINES":"ENGACT-001",
    "BOOTSTRAP_CRM":"CRMBOOT-001",
    "BOOTSTRAP_APP":"APPBOOT-001",
    "BOOTSTRAP_AUTOMATIONS":"AUTBOOT-001",
    "BOOTSTRAP_TRAINING":"TRNBOOT-001",
    "CREATE_SUPERVISOR_SCOPE":"COMP-HLT-001",
    "CREATE_BACKUP_REBUILD_PACK":"COMP-BKP-001",
    "PREPROD_TESTS":"COMP-DEP-001",
    "PRODUCTION_ACTIVATION":"COMP-ONB-001",
}

@dataclass(frozen=True)
class PhaseState:
    phase:str
    status:str
    attempt:int
    evidence_ref:str=""
    reason:str=""

def _event_id(company_id:str,phase:str,attempt:int)->str:
    raw=f"{company_id}|{phase}|{attempt}"
    return "onb-"+hashlib.sha256(raw.encode()).hexdigest()[:24]

def initial_state(company_id:str,version:str="1.0.0")->dict:
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id and version required")
    return {
        "record_type":"company_onboarding_state",
        "company_id":company_id,
        "engine_id":"COMP-ONB-001",
        "environment":"LAB",
        "version":version,
        "status":"IN_PROGRESS",
        "current_phase":PHASES[0],
        "phases":[asdict(PhaseState(p,"PENDING",0)) for p in PHASES],
        "production_activation_allowed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def advance(state:dict, phase_result:dict)->dict:
    company_id=str(state.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    current=str(state.get("current_phase","")).strip()
    if current not in PHASES: raise ValueError("invalid current phase")
    if str(phase_result.get("company_id",""))!=company_id:
        raise ValueError("cross-company phase result denied")
    if str(phase_result.get("phase",""))!=current:
        raise ValueError("phase result mismatch")
    status=str(phase_result.get("status","")).upper()
    if status not in {"GREEN","WAITING","HUMAN_REQUIRED","BLOCKED"}:
        raise ValueError("unsupported phase status")

    rows=[dict(x) for x in state.get("phases") or []]
    idx=PHASES.index(current)
    row=rows[idx]
    attempt=int(row.get("attempt",0))+1
    row.update({
        "status":status,
        "attempt":attempt,
        "evidence_ref":str(phase_result.get("evidence_ref","")),
        "reason":str(phase_result.get("reason","")),
        "event_id":_event_id(company_id,current,attempt),
    })
    rows[idx]=row

    if status=="GREEN":
        if current=="PRODUCTION_ACTIVATION":
            # V0 can only prepare this gate, never authorize PROD.
            row["status"]="HUMAN_REQUIRED"
            row["reason"]="HIGH_RISK"
            rows[idx]=row
            return {**state,"phases":rows,"status":"HUMAN_REQUIRED","human_reason":"HIGH_RISK","production_activation_allowed":False}
        next_phase=PHASES[idx+1] if idx+1<len(PHASES) else None
        return {**state,"phases":rows,"current_phase":next_phase,"status":"GREEN" if next_phase is None else "IN_PROGRESS"}
    if status=="HUMAN_REQUIRED":
        reason=str(phase_result.get("human_reason") or phase_result.get("reason") or "LOW_CONFIDENCE")
        if reason not in {"LEGAL_REQUIRED","SIGNATURE_REQUIRED","LOW_CONFIDENCE","HIGH_RISK","POLICY_CONFLICT","SECURITY_INCIDENT","MONEY_LIMIT","CUSTOMER_HUMAN_REQUEST"}:
            raise ValueError("invalid HUMAN_REQUIRED reason")
        return {**state,"phases":rows,"status":"HUMAN_REQUIRED","human_reason":reason}
    return {**state,"phases":rows,"status":status}

def default_phase_plan(state:dict)->dict:
    phase=str(state["current_phase"])
    company_id=str(state["company_id"])
    target_engine_id=PHASE_ENGINE_MAP.get(phase)
    if not target_engine_id:
        raise ValueError("phase engine binding missing")
    if phase=="MINIMUM_ACCESSES":
        return {
            "company_id":company_id,"engine_id":"COMP-ONB-001","phase":phase,
            "target_engine_id":target_engine_id,
            "execution_mode":"LOCAL_DETERMINISTIC","environment":"LAB",
            "allowed_external_mutation":False,"required_cost_eur":0.0,
            "required_gates":["TENANT-001","IAM-001","POL-001"],
        }
    if phase in READ_ONLY_DISCOVERY:
        return {
            "company_id":company_id,"engine_id":"COMP-ONB-001","phase":phase,
            "target_engine_id":target_engine_id,
            "execution_mode":"READ_ONLY","environment":"LAB",
            "allowed_external_mutation":False,"required_cost_eur":0.0,
            "required_gates":["TENANT-001","PRV-001","OBSERV-001"],
        }
    if phase in PREPROD_ONLY:
        return {
            "company_id":company_id,"engine_id":"COMP-ONB-001","phase":phase,
            "target_engine_id":target_engine_id,
            "execution_mode":"PREPROD_ONLY","environment":"PREPROD",
            "allowed_external_mutation":False,"required_cost_eur":0.0,
            "required_gates":["TENANT-001","QA-001","REG-001","DR-001","RBLD-001"],
        }
    if phase=="PRODUCTION_ACTIVATION":
        return {
            "company_id":company_id,"engine_id":"COMP-ONB-001","phase":phase,
            "target_engine_id":target_engine_id,
            "execution_mode":"GATE_ONLY","environment":"PREPROD",
            "allowed_external_mutation":False,"required_cost_eur":0.0,
            "required_gates":["QA-001","QAB-001","REG-001","EVA-001","JDG-001","OBSERV-001","DR-001","RBLD-001","TENANT-001"],
            "production_activation_allowed":False,
        }
    return {
        "company_id":company_id,"engine_id":"COMP-ONB-001","phase":phase,
        "target_engine_id":target_engine_id,
        "execution_mode":"LOCAL_DETERMINISTIC","environment":"LAB",
        "allowed_external_mutation":False,"required_cost_eur":0.0,
        "required_gates":["TENANT-001","OBSERV-001"],
    }

def run()->list[Path]:
    request_root=Path(os.environ.get("CEREBRO_COMPANY_ONBOARD_REQUEST_ROOT",".cerebro-runtime/company-onboard-requests"))
    state_root=Path(os.environ.get("CEREBRO_COMPANY_ONBOARD_STATE_ROOT",".cerebro-runtime/company-onboarding"))
    state_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(request_root.glob("*.json")):
        req=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(req,dict): raise ValueError("onboarding request must be object")
        company_id=str(req.get("company_id","")).strip()
        if not company_id: raise ValueError("company_id required")
        target=state_root/f"{company_id}.json"
        state=json.loads(target.read_text(encoding="utf-8")) if target.exists() else initial_state(company_id,str(req.get("version","1.0.0")))
        plan=default_phase_plan(state)
        body={**state,"next_execution_plan":plan}
        target.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
