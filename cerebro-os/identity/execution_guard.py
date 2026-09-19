from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionGuardRequest:
    company_id:str
    engine_id:str
    account_id:str
    environment:str
    version:str
    action:str
    kill_switch_enabled:bool
    audit_sink_available:bool
    policy_green:bool
    idempotency_key:str
    credential_reference_available:bool

    def validate(self)->None:
        required=(self.company_id,self.engine_id,self.account_id,self.environment,self.version,self.action,self.idempotency_key)
        if not all(str(x).strip() for x in required):
            raise ValueError("execution guard scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")

def evaluate_execution_guard(req:ExecutionGuardRequest)->dict:
    req.validate()
    blockers=[]
    human_reason=None
    if not req.kill_switch_enabled:
        blockers.append("KILL_SWITCH_REQUIRED")
    if not req.audit_sink_available:
        blockers.append("AUDIT_SINK_REQUIRED")
    if not req.policy_green:
        blockers.append("POLICY_NOT_GREEN")
        human_reason="POLICY_CONFLICT"
    if not req.credential_reference_available:
        blockers.append("CREDENTIAL_REFERENCE_MISSING")
    allowed=not blockers and req.environment!="PROD"
    if req.environment=="PROD":
        blockers.append("PROD_EXECUTION_GATE_REQUIRED")
    return {
      "company_id":req.company_id,"engine_id":req.engine_id,"account_id":req.account_id,
      "environment":req.environment,"version":req.version,"action":req.action,
      "status":"GREEN" if allowed else "HUMAN_REQUIRED" if human_reason else "BLOCKED",
      "execution_allowed":allowed,"production_execution_allowed":False,
      "kill_switch_required":True,"audit_log_required":True,
      "idempotency_key":req.idempotency_key,
      "secret_value_exposure_allowed":False,
      "external_mutation_allowed":False,
      "blockers":tuple(blockers),"human_reason":human_reason,"cost_eur":0.0,
    }
