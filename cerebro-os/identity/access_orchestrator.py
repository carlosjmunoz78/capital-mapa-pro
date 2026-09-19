from __future__ import annotations

from dataclasses import dataclass
from account_registry import IdentityAccountRegistry
from credential_scope import ScopedCredentialRef, authorize_credential_ref
from connector_registry import ConnectorRegistry
from computer_use_policy import ComputerUseRequest, evaluate_computer_use

@dataclass(frozen=True)
class AccessExecutionRequest:
    company_id:str
    identity_id:str
    account_id:str
    engine_id:str
    capability:str
    action:str
    environment:str="LAB"
    version:str="1.0.0"
    policy_green:bool=True
    confidence:float=1.0
    money_amount:float=0.0
    money_limit:float=0.0
    explicit_customer_human_request:bool=False

    def validate(self)->None:
        required=(self.company_id,self.identity_id,self.account_id,self.engine_id,self.capability,self.action,self.environment,self.version)
        if not all(str(x).strip() for x in required):
            raise ValueError("access execution scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")
        if not 0<=self.confidence<=1:
            raise ValueError("confidence must be between 0 and 1")

def plan_access_execution(
    req:AccessExecutionRequest,
    *,
    registry:IdentityAccountRegistry,
    credential:ScopedCredentialRef|None,
    connectors:ConnectorRegistry,
)->dict:
    req.validate()
    account=registry.account(req.company_id,req.account_id,req.environment,req.version)
    if account.identity_id!=req.identity_id:
        raise PermissionError("identity/account mismatch")

    credential_ready=False
    credential_meta=None
    if credential is not None:
        credential_meta=authorize_credential_ref(
            credential=credential,
            company_id=req.company_id,
            identity_id=req.identity_id,
            account_id=req.account_id,
            environment=req.environment,
            version=req.version,
        )
        credential_ready=True

    connector=connectors.route(req.company_id,req.capability,req.environment,req.version)
    if connector and connector.connector_type not in {"BROWSER","COMPUTER_USE"}:
        return {
          "status":"GREEN",
          "decision":"USE_HIGHER_PRIORITY_CONNECTOR",
          "connector_id":connector.connector_id,
          "connector_type":connector.connector_type,
          "company_id":req.company_id,
          "identity_id":req.identity_id,
          "account_id":req.account_id,
          "credential_reference_available":credential_ready,
          "secret_value_exposed":False,
          "browser_fallback_allowed":False,
          "computer_use_allowed":False,
          "external_mutation_allowed":False,
        }

    computer=evaluate_computer_use(ComputerUseRequest(
        company_id=req.company_id,
        engine_id=req.engine_id,
        environment=req.environment,
        version=req.version,
        capability=req.capability,
        action=req.action,
        higher_priority_connector_available=False,
        account_registered=True,
        credential_reference_available=credential_ready,
        policy_green=req.policy_green,
        confidence=req.confidence,
        money_amount=req.money_amount,
        money_limit=req.money_limit,
        explicit_customer_human_request=req.explicit_customer_human_request,
    ))
    return {
      **computer,
      "status":"HUMAN_REQUIRED" if computer["human_required"] else "BLOCKED" if computer["blockers"] else "GREEN",
      "decision":"COMPUTER_USE_FALLBACK" if computer["computer_use_allowed"] else "ACCESS_BLOCKED",
      "connector_id":connector.connector_id if connector else None,
      "connector_type":connector.connector_type if connector else None,
      "company_id":req.company_id,
      "identity_id":req.identity_id,
      "account_id":req.account_id,
      "credential_reference_available":credential_ready,
      "secret_value_exposed":False,
      "external_mutation_allowed":False,
      "credential_meta":credential_meta,
    }
