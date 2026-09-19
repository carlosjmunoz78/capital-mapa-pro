from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}
VALID_LOGIN_METHODS={"EMAIL_PASSWORD","GOOGLE","MICROSOFT","APPLE","SOCIAL","PASSKEY","OAUTH","SSO","SESSION","API_KEY","TOKEN","OTHER"}

@dataclass(frozen=True)
class SessionObservation:
    company_id:str
    provider:str
    environment:str
    version:str
    authenticated:bool
    login_method:str
    account_hint:str=""
    profile_id:str=""
    browser_family:str=""
    device_id:str=""
    evidence_ref:str=""
    secret_value_observed:bool=False

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.company_id,self.provider,self.environment,self.version,self.login_method)):
            raise ValueError("session observation scope required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid session environment")
        if self.login_method not in VALID_LOGIN_METHODS:
            raise ValueError("unsupported login method")
        if self.secret_value_observed:
            raise ValueError("secret extraction is forbidden")

def discover_session_metadata(obs:SessionObservation)->dict:
    obs.validate()
    status="AUTHENTICATED_SESSION_DISCOVERED" if obs.authenticated else "LOGIN_REQUIRED"
    confidence=0.95 if obs.authenticated and obs.evidence_ref else 0.75 if obs.authenticated else 0.6
    return {
      "record_type":"session_discovery",
      "company_id":obs.company_id,
      "provider":obs.provider,
      "environment":obs.environment,
      "version":obs.version,
      "status":status,
      "authenticated":obs.authenticated,
      "login_method":obs.login_method,
      "account_hint":obs.account_hint,
      "profile_id":obs.profile_id,
      "browser_family":obs.browser_family,
      "device_id":obs.device_id,
      "evidence_ref":obs.evidence_ref,
      "confidence":confidence,
      "password_recovery_attempted":False,
      "secret_value_exposed":False,
      "secret_extraction_allowed":False,
      "credential_reference_required_for_execution":True,
      "external_mutation_allowed":False,
      "cost_eur":0.0,
    }
