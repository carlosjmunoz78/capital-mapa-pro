from __future__ import annotations

from dataclasses import dataclass

from account_registry import IdentityAccountRegistry
from credential_scope import ScopedCredentialRef
from connector_registry import ConnectorRegistry
from access_orchestrator import AccessExecutionRequest, plan_access_execution
from multiaccount_session_registry import MultiAccountSessionRegistry
from execution_guard import ExecutionGuardRequest, evaluate_execution_guard
from browser_bridge_handoff import build_bridge_handoff
from browser_bridge_control import BrowserBridgeCommand, BrowserBridgeRegistry, evaluate_bridge_command
from browser_bridge_runtime import BridgeRuntimeState, evaluate_bridge_runtime_dispatch

@dataclass(frozen=True)
class AccessOperationRequest:
    request_id:str
    company_id:str
    identity_id:str
    account_id:str
    engine_id:str
    capability:str
    action:str
    environment:str
    version:str
    idempotency_key:str
    audit_ref:str
    policy_green:bool=True
    confidence:float=1.0
    money_amount:float=0.0
    money_limit:float=0.0
    explicit_customer_human_request:bool=False

    def validate(self)->None:
        required=(
            self.request_id,self.company_id,self.identity_id,self.account_id,self.engine_id,
            self.capability,self.action,self.environment,self.version,self.idempotency_key,self.audit_ref
        )
        if not all(str(x).strip() for x in required):
            raise ValueError("access operation scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")
        if not 0<=self.confidence<=1:
            raise ValueError("confidence must be between 0 and 1")
        if self.money_amount<0 or self.money_limit<0:
            raise ValueError("money values must be non-negative")

def plan_access_operation(
    req:AccessOperationRequest,
    *,
    account_registry:IdentityAccountRegistry,
    credential:ScopedCredentialRef|None,
    connectors:ConnectorRegistry,
    sessions:MultiAccountSessionRegistry,
    bridge_registry:BrowserBridgeRegistry,
    runtime_state:BridgeRuntimeState,
    now_epoch:int,
    max_heartbeat_age_seconds:int=120,
)->dict:
    req.validate()

    access=plan_access_execution(
        AccessExecutionRequest(
            company_id=req.company_id,identity_id=req.identity_id,account_id=req.account_id,
            engine_id=req.engine_id,capability=req.capability,action=req.action,
            environment=req.environment,version=req.version,policy_green=req.policy_green,
            confidence=req.confidence,money_amount=req.money_amount,money_limit=req.money_limit,
            explicit_customer_human_request=req.explicit_customer_human_request,
        ),
        registry=account_registry,credential=credential,connectors=connectors,
    )

    base={
        "record_type":"access_operation_plan","engine_id":"OPACCESS-001",
        "request_id":req.request_id,"company_id":req.company_id,"identity_id":req.identity_id,
        "account_id":req.account_id,"environment":req.environment,"version":req.version,
        "capability":req.capability,"action":req.action,"idempotency_key":req.idempotency_key,
        "audit_ref":req.audit_ref,"external_mutation_performed":False,"cost_eur":0.0,
    }

    if access.get("status")!="GREEN":
        return {**base,"status":access.get("status","BLOCKED"),"decision":"ACCESS_NOT_READY","access_plan":access,"dispatch_candidate":None}

    if access.get("decision")=="USE_HIGHER_PRIORITY_CONNECTOR":
        if req.environment=="PROD":
            return {
                **base,"status":"HUMAN_REQUIRED","decision":"PROD_CONNECTOR_EXECUTION_GATE_REQUIRED",
                "human_reason":"HIGH_RISK","access_plan":access,"dispatch_candidate":None,
            }
        return {
            **base,"status":"GREEN","decision":"CONNECTOR_EXECUTION_CANDIDATE",
            "connector_id":access.get("connector_id"),"connector_type":access.get("connector_type"),
            "access_plan":access,"dispatch_candidate":None,
        }

    if access.get("decision")!="COMPUTER_USE_FALLBACK":
        return {**base,"status":"BLOCKED","decision":"UNSUPPORTED_ACCESS_DECISION","access_plan":access,"dispatch_candidate":None}

    session=sessions.resolve_authenticated(req.company_id,req.account_id,req.environment,req.version)
    if session is None:
        return {
            **base,"status":"BLOCKED","decision":"AUTHENTICATED_SESSION_REQUIRED",
            "access_plan":access,"dispatch_candidate":None,
        }
    sessions.assert_scope(
        session,company_id=req.company_id,identity_id=req.identity_id,account_id=req.account_id,
        environment=req.environment,version=req.version,
    )

    guard=evaluate_execution_guard(ExecutionGuardRequest(
        company_id=req.company_id,engine_id=req.engine_id,account_id=req.account_id,
        environment=req.environment,version=req.version,action=req.action,
        kill_switch_enabled=True,audit_sink_available=True,policy_green=req.policy_green,
        idempotency_key=req.idempotency_key,credential_reference_available=credential is not None,
    ))
    if guard.get("status")!="GREEN":
        return {
            **base,"status":guard.get("status","BLOCKED"),"decision":"EXECUTION_GUARD_NOT_GREEN",
            "access_plan":access,"guard":guard,"dispatch_candidate":None,
        }

    session_payload={
        "company_id":session.company_id,"account_id":session.account_id,
        "authenticated":session.authenticated,"profile_id":session.profile_id,"device_id":session.device_id,
    }
    handoff=build_bridge_handoff(
        access_plan=access,session=session_payload,guard=guard,
        request_id=req.request_id,audit_ref=req.audit_ref,
    )
    if handoff.get("status")!="GREEN":
        return {
            **base,"status":"BLOCKED","decision":"BRIDGE_HANDOFF_NOT_GREEN",
            "access_plan":access,"guard":guard,"handoff":handoff,"dispatch_candidate":None,
        }

    candidate=dict(handoff["dispatch_candidate"])
    candidate["engine_id"]=req.engine_id
    candidate["capability"]=req.capability
    candidate["action"]=req.action
    candidate["policy_green"]=req.policy_green
    candidate["confidence"]=req.confidence
    candidate["credential_reference_available"]=credential is not None

    bridge=evaluate_bridge_command(BrowserBridgeCommand(**candidate),bridge_registry)
    if bridge.get("status")!="GREEN":
        return {
            **base,"status":bridge.get("status","BLOCKED"),"decision":"BRIDGE_CONTROL_NOT_GREEN",
            "access_plan":access,"guard":guard,"handoff":handoff,"bridge_control":bridge,
            "dispatch_candidate":None,
        }

    runtime=evaluate_bridge_runtime_dispatch(
        state=runtime_state,command=candidate,now_epoch=now_epoch,
        max_heartbeat_age_seconds=max_heartbeat_age_seconds,
    )
    if runtime.get("status")!="GREEN" or not runtime.get("dispatch_allowed"):
        return {
            **base,"status":runtime.get("status","BLOCKED"),"decision":"BRIDGE_RUNTIME_NOT_READY",
            "access_plan":access,"guard":guard,"bridge_control":bridge,"runtime":runtime,
            "dispatch_candidate":None,
        }

    return {
        **base,"status":"GREEN","decision":"BRIDGE_DISPATCH_CANDIDATE",
        "access_plan":access,"guard":guard,"bridge_control":bridge,"runtime":runtime,
        "dispatch_candidate":candidate,"credential_value_included":False,"secret_value_included":False,
    }
