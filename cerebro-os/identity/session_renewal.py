from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionRenewalRequest:
    company_id:str
    identity_id:str
    account_id:str
    provider:str
    environment:str
    version:str
    authenticated:bool
    renewable_without_secret_exposure:bool
    higher_priority_connector_available:bool
    policy_green:bool
    confidence:float
    requires_human_mfa:bool=False
    requires_legal_acceptance:bool=False

    def validate(self)->None:
        required=(self.company_id,self.identity_id,self.account_id,self.provider,self.environment,self.version)
        if not all(str(x).strip() for x in required):
            raise ValueError("session renewal scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")
        if not 0<=self.confidence<=1:
            raise ValueError("confidence must be between 0 and 1")

def plan_session_renewal(req:SessionRenewalRequest)->dict:
    req.validate()
    if req.authenticated:
        return {
          "status":"GREEN","decision":"KEEP_EXISTING_AUTHENTICATED_SESSION",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":None,
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if req.higher_priority_connector_available:
        return {
          "status":"GREEN","decision":"USE_HIGHER_PRIORITY_CONNECTOR",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":None,
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if not req.policy_green:
        return {
          "status":"HUMAN_REQUIRED","decision":"POLICY_BLOCK",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":"POLICY_CONFLICT",
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if req.requires_legal_acceptance:
        return {
          "status":"HUMAN_REQUIRED","decision":"LEGAL_ACCEPTANCE_REQUIRED",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":"LEGAL_REQUIRED",
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if req.requires_human_mfa:
        return {
          "status":"HUMAN_REQUIRED","decision":"HUMAN_MFA_REQUIRED",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":"HIGH_RISK",
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if req.confidence<0.85:
        return {
          "status":"HUMAN_REQUIRED","decision":"LOW_CONFIDENCE",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":"LOW_CONFIDENCE",
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    if not req.renewable_without_secret_exposure:
        return {
          "status":"BLOCKED","decision":"SAFE_RENEWAL_UNAVAILABLE",
          "renewal_allowed":False,"browser_login_allowed":False,"human_reason":None,
          "secret_value_exposure_allowed":False,"cost_eur":0.0,
        }
    return {
      "status":"GREEN","decision":"SAFE_SESSION_RENEWAL_CANDIDATE",
      "renewal_allowed":req.environment!="PROD",
      "production_renewal_allowed":False,
      "browser_login_allowed":req.environment!="PROD",
      "secret_value_exposure_allowed":False,
      "external_mutation_allowed":False,
      "human_reason":None,"cost_eur":0.0,
    }
