from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}

@dataclass(frozen=True)
class BrowserBridgeDevice:
    device_id:str
    company_id:str
    profile_id:str
    browser_family:str
    environment:str="LAB"
    version:str="1.0.0"
    paired:bool=False
    online:bool=False
    kill_switch_enabled:bool=True
    status:str="ACTIVE"

    def validate(self)->None:
        required=(self.device_id,self.company_id,self.profile_id,self.browser_family,self.environment,self.version)
        if not all(str(x).strip() for x in required):
            raise ValueError("browser bridge device scope required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid bridge environment")

@dataclass(frozen=True)
class BrowserBridgeCommand:
    request_id:str
    company_id:str
    identity_id:str
    account_id:str
    engine_id:str
    capability:str
    action:str
    device_id:str
    profile_id:str
    environment:str="LAB"
    version:str="1.0.0"
    idempotency_key:str=""
    audit_ref:str=""
    policy_green:bool=True
    confidence:float=1.0
    credential_reference_available:bool=False
    human_reason:str|None=None

    def validate(self)->None:
        required=(self.request_id,self.company_id,self.identity_id,self.account_id,self.engine_id,self.capability,self.action,self.device_id,self.profile_id,self.environment,self.version,self.idempotency_key,self.audit_ref)
        if not all(str(x).strip() for x in required):
            raise ValueError("browser bridge command scope required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid bridge command environment")
        if not 0<=self.confidence<=1:
            raise ValueError("confidence must be between 0 and 1")

@dataclass
class BrowserBridgeRegistry:
    devices:List[BrowserBridgeDevice]=field(default_factory=list)

    def register(self,item:BrowserBridgeDevice)->None:
        item.validate()
        if any(x.device_id==item.device_id and x.environment==item.environment and x.version==item.version for x in self.devices):
            raise ValueError("duplicate bridge device scope")
        self.devices.append(item)

    def resolve(self,*,company_id:str,device_id:str,profile_id:str,environment:str,version:str)->BrowserBridgeDevice:
        matches=[
            x for x in self.devices
            if x.company_id==company_id and x.device_id==device_id and x.profile_id==profile_id
            and x.environment==environment and x.version==version and x.status=="ACTIVE"
        ]
        if not matches:
            raise KeyError(device_id)
        return matches[0]

def evaluate_bridge_command(command:BrowserBridgeCommand,registry:BrowserBridgeRegistry)->dict:
    command.validate()
    try:
        device=registry.resolve(
            company_id=command.company_id,device_id=command.device_id,profile_id=command.profile_id,
            environment=command.environment,version=command.version
        )
    except KeyError:
        return {
          "status":"BLOCKED","decision":"BRIDGE_DEVICE_NOT_REGISTERED","dispatch_allowed":False,
          "human_reason":None,"blockers":("BRIDGE_DEVICE_NOT_REGISTERED",),
          "credential_value_exposure_allowed":False,"secret_copy_to_prompt_allowed":False,
          "external_mutation_allowed":False,"cost_eur":0.0,
        }

    blockers=[]
    human_reason=command.human_reason
    if not device.paired:
        blockers.append("BRIDGE_NOT_PAIRED")
    if not device.online:
        blockers.append("BRIDGE_OFFLINE")
    if not device.kill_switch_enabled:
        blockers.append("KILL_SWITCH_REQUIRED")
    if not command.policy_green:
        blockers.append("POLICY_NOT_GREEN")
        human_reason=human_reason or "POLICY_CONFLICT"
    if command.confidence<0.85:
        blockers.append("LOW_CONFIDENCE")
        human_reason=human_reason or "LOW_CONFIDENCE"
    if not command.credential_reference_available:
        blockers.append("CREDENTIAL_REFERENCE_MISSING")
    if command.environment=="PROD":
        blockers.append("PROD_BRIDGE_EXECUTION_GATE_REQUIRED")
        human_reason=human_reason or "HIGH_RISK"

    allowed=not blockers
    return {
      "status":"GREEN" if allowed else "HUMAN_REQUIRED" if human_reason else "BLOCKED",
      "decision":"DISPATCH_BRIDGE_COMMAND" if allowed else "BRIDGE_COMMAND_BLOCKED",
      "dispatch_allowed":allowed,
      "company_id":command.company_id,"identity_id":command.identity_id,"account_id":command.account_id,
      "engine_id":command.engine_id,"device_id":command.device_id,"profile_id":command.profile_id,
      "environment":command.environment,"version":command.version,"request_id":command.request_id,
      "idempotency_key":command.idempotency_key,"audit_ref":command.audit_ref,
      "kill_switch_required":True,"audit_log_required":True,
      "credential_value_exposure_allowed":False,"secret_copy_to_prompt_allowed":False,
      "external_mutation_allowed":False,
      "human_reason":human_reason,"blockers":tuple(blockers),"cost_eur":0.0,
    }
