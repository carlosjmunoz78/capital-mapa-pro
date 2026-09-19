from __future__ import annotations

from dataclasses import dataclass

HUMAN_ONLY_REQUIREMENTS={"PHONE_OTP","CAPTCHA","IDENTITY_VERIFICATION","LEGAL_ACCEPTANCE","BINDING_SIGNATURE","HUMAN_MFA"}

@dataclass(frozen=True)
class AccountLifecycleRequest:
    company_id:str
    identity_id:str
    provider:str
    purpose:str
    environment:str
    version:str
    existing_reusable_account:bool
    policy_green:bool
    required_human_steps:tuple[str,...]=()
    money_amount:float=0.0
    money_limit:float=0.0

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.company_id,self.identity_id,self.provider,self.purpose,self.environment,self.version)):
            raise ValueError("account lifecycle scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")
        if self.money_amount<0 or self.money_limit<0:
            raise ValueError("money values must be non-negative")

def plan_account_lifecycle(req:AccountLifecycleRequest)->dict:
    req.validate()
    if req.existing_reusable_account:
        return {"status":"GREEN","decision":"REUSE_EXISTING_ACCOUNT","create_account_allowed":False,"human_reason":None,"cost_eur":0.0}
    if not req.policy_green:
        return {"status":"HUMAN_REQUIRED","decision":"BLOCKED_BY_POLICY","create_account_allowed":False,"human_reason":"POLICY_CONFLICT","cost_eur":0.0}
    if req.money_amount>req.money_limit:
        return {"status":"HUMAN_REQUIRED","decision":"MONEY_LIMIT","create_account_allowed":False,"human_reason":"MONEY_LIMIT","cost_eur":0.0}
    human=[x for x in req.required_human_steps if x in HUMAN_ONLY_REQUIREMENTS]
    if human:
        reason="SIGNATURE_REQUIRED" if "BINDING_SIGNATURE" in human else "LEGAL_REQUIRED" if "LEGAL_ACCEPTANCE" in human else "HIGH_RISK"
        return {"status":"HUMAN_REQUIRED","decision":"HUMAN_STEP_REQUIRED","create_account_allowed":False,"human_reason":reason,"required_human_steps":tuple(human),"cost_eur":0.0}
    return {
      "status":"GREEN","decision":"CREATE_ACCOUNT_CANDIDATE","create_account_allowed":req.environment!="PROD",
      "production_creation_allowed":False,"external_mutation_allowed":False,"human_reason":None,"cost_eur":0.0,
    }
