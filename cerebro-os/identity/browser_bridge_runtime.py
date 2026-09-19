from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class BridgeHeartbeat:
    device_id:str
    company_id:str
    profile_id:str
    environment:str
    version:str
    observed_at_epoch:int
    online:bool
    paired:bool
    kill_switch_enabled:bool

    def validate(self)->None:
        required=(self.device_id,self.company_id,self.profile_id,self.environment,self.version)
        if not all(str(x).strip() for x in required):
            raise ValueError("heartbeat scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid heartbeat environment")
        if self.observed_at_epoch<0:
            raise ValueError("invalid heartbeat timestamp")

@dataclass(frozen=True)
class DispatchReceipt:
    request_id:str
    idempotency_key:str
    device_id:str
    company_id:str
    environment:str
    version:str
    status:str
    observed_at_epoch:int
    evidence_ref:str=""

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.request_id,self.idempotency_key,self.device_id,self.company_id,self.environment,self.version,self.status)):
            raise ValueError("dispatch receipt fields required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid receipt environment")
        if self.observed_at_epoch<0:
            raise ValueError("invalid receipt timestamp")

@dataclass
class BridgeRuntimeState:
    heartbeats:Dict[tuple[str,str,str,str],BridgeHeartbeat]=field(default_factory=dict)
    receipts:Dict[str,DispatchReceipt]=field(default_factory=dict)

    def record_heartbeat(self,item:BridgeHeartbeat)->None:
        item.validate()
        key=(item.company_id,item.device_id,item.environment,item.version)
        current=self.heartbeats.get(key)
        if current and item.observed_at_epoch<current.observed_at_epoch:
            raise ValueError("stale heartbeat rejected")
        self.heartbeats[key]=item

    def heartbeat(self,*,company_id:str,device_id:str,environment:str,version:str)->BridgeHeartbeat|None:
        return self.heartbeats.get((company_id,device_id,environment,version))

    def record_receipt(self,item:DispatchReceipt)->None:
        item.validate()
        existing=self.receipts.get(item.idempotency_key)
        if existing and existing.request_id!=item.request_id:
            raise ValueError("idempotency key conflict")
        if existing and item.observed_at_epoch<existing.observed_at_epoch:
            raise ValueError("stale dispatch receipt rejected")
        self.receipts[item.idempotency_key]=item

    def receipt(self,idempotency_key:str)->DispatchReceipt|None:
        return self.receipts.get(idempotency_key)

def evaluate_bridge_runtime_dispatch(*,state:BridgeRuntimeState,command:dict,now_epoch:int,max_heartbeat_age_seconds:int=120)->dict:
    if now_epoch<0 or max_heartbeat_age_seconds<1:
        raise ValueError("invalid runtime timing")
    company_id=str(command.get("company_id","")).strip()
    device_id=str(command.get("device_id","")).strip()
    environment=str(command.get("environment","")).strip()
    version=str(command.get("version","")).strip()
    idem=str(command.get("idempotency_key","")).strip()
    if not all((company_id,device_id,environment,version,idem)):
        raise ValueError("dispatch runtime scope required")

    prior=state.receipt(idem)
    if prior and prior.status in {"ACKNOWLEDGED","COMPLETED"}:
        return {
          "status":"GREEN","decision":"IDEMPOTENT_REPLAY_SUPPRESSED","dispatch_allowed":False,
          "receipt_status":prior.status,"receipt_evidence_ref":prior.evidence_ref,
          "human_reason":None,"cost_eur":0.0,
        }

    hb=state.heartbeat(company_id=company_id,device_id=device_id,environment=environment,version=version)
    if hb is None:
        return {"status":"BLOCKED","decision":"HEARTBEAT_MISSING","dispatch_allowed":False,"human_reason":None,"cost_eur":0.0}

    age=now_epoch-hb.observed_at_epoch
    if age<0:
        return {"status":"BLOCKED","decision":"HEARTBEAT_FROM_FUTURE","dispatch_allowed":False,"human_reason":None,"cost_eur":0.0}
    if age>max_heartbeat_age_seconds:
        return {"status":"BLOCKED","decision":"HEARTBEAT_STALE","dispatch_allowed":False,"heartbeat_age_seconds":age,"human_reason":None,"cost_eur":0.0}
    if not hb.online:
        return {"status":"BLOCKED","decision":"BRIDGE_OFFLINE","dispatch_allowed":False,"human_reason":None,"cost_eur":0.0}
    if not hb.paired:
        return {"status":"BLOCKED","decision":"BRIDGE_NOT_PAIRED","dispatch_allowed":False,"human_reason":None,"cost_eur":0.0}
    if not hb.kill_switch_enabled:
        return {"status":"BLOCKED","decision":"KILL_SWITCH_REQUIRED","dispatch_allowed":False,"human_reason":None,"cost_eur":0.0}
    if environment=="PROD":
        return {"status":"HUMAN_REQUIRED","decision":"PROD_RUNTIME_GATE_REQUIRED","dispatch_allowed":False,"human_reason":"HIGH_RISK","cost_eur":0.0}

    return {
      "status":"GREEN","decision":"DISPATCH_RUNTIME_READY","dispatch_allowed":True,
      "heartbeat_age_seconds":age,"human_reason":None,
      "audit_log_required":True,"receipt_required":True,"cost_eur":0.0,
    }
