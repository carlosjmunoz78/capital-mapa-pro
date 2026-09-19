from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}
TERMINAL_STATUSES={"COMPLETED","FAILED","CANCELLED"}

@dataclass(frozen=True)
class BridgeDispatch:
    command_id:str
    request_id:str
    company_id:str
    identity_id:str
    account_id:str
    engine_id:str
    capability:str
    action:str
    device_id:str
    profile_id:str
    environment:str
    version:str
    idempotency_key:str
    audit_ref:str
    created_at_epoch:int
    expires_at_epoch:int

    def validate(self)->None:
        required=(self.command_id,self.request_id,self.company_id,self.identity_id,self.account_id,self.engine_id,self.capability,self.action,self.device_id,self.profile_id,self.environment,self.version,self.idempotency_key,self.audit_ref)
        if not all(str(x).strip() for x in required):
            raise ValueError("bridge dispatch fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid dispatch environment")
        if self.created_at_epoch<0 or self.expires_at_epoch<=self.created_at_epoch:
            raise ValueError("invalid dispatch validity window")

@dataclass(frozen=True)
class BridgeAck:
    command_id:str
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
        if not all(str(x).strip() for x in (self.command_id,self.request_id,self.idempotency_key,self.device_id,self.company_id,self.environment,self.version,self.status)):
            raise ValueError("bridge ack fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid ack environment")
        if self.observed_at_epoch<0:
            raise ValueError("invalid ack timestamp")

@dataclass
class BridgeCommandQueue:
    pending:List[BridgeDispatch]=field(default_factory=list)
    status_by_command:Dict[str,str]=field(default_factory=dict)
    ack_by_command:Dict[str,BridgeAck]=field(default_factory=dict)
    command_by_idempotency:Dict[str,str]=field(default_factory=dict)

    def enqueue(self,item:BridgeDispatch)->None:
        item.validate()
        if item.command_id in self.status_by_command:
            raise ValueError("duplicate command_id")
        existing=self.command_by_idempotency.get(item.idempotency_key)
        if existing and existing!=item.command_id:
            raise ValueError("duplicate idempotency key")
        self.pending.append(item)
        self.status_by_command[item.command_id]="QUEUED"
        self.command_by_idempotency[item.idempotency_key]=item.command_id

    def claim(self,*,company_id:str,device_id:str,environment:str,version:str,now_epoch:int)->BridgeDispatch|None:
        if now_epoch<0:
            raise ValueError("invalid claim time")
        candidates=[]
        for item in self.pending:
            if self.status_by_command.get(item.command_id)!="QUEUED":
                continue
            if item.company_id!=company_id or item.device_id!=device_id or item.environment!=environment or item.version!=version:
                continue
            if now_epoch>item.expires_at_epoch:
                self.status_by_command[item.command_id]="EXPIRED"
                continue
            candidates.append(item)
        if not candidates:
            return None
        selected=sorted(candidates,key=lambda x:(x.created_at_epoch,x.command_id))[0]
        self.status_by_command[selected.command_id]="CLAIMED"
        return selected

    def acknowledge(self,ack:BridgeAck)->None:
        ack.validate()
        status=self.status_by_command.get(ack.command_id)
        if status is None:
            raise KeyError(ack.command_id)
        dispatch=next(x for x in self.pending if x.command_id==ack.command_id)
        if (
            ack.request_id!=dispatch.request_id or ack.idempotency_key!=dispatch.idempotency_key or
            ack.device_id!=dispatch.device_id or ack.company_id!=dispatch.company_id or
            ack.environment!=dispatch.environment or ack.version!=dispatch.version
        ):
            raise PermissionError("bridge ack scope mismatch")
        if status in TERMINAL_STATUSES:
            prior=self.ack_by_command.get(ack.command_id)
            if prior and prior.status==ack.status and prior.request_id==ack.request_id:
                return
            raise ValueError("terminal command cannot transition")
        if ack.status not in {"ACKNOWLEDGED","IN_PROGRESS","COMPLETED","FAILED","CANCELLED"}:
            raise ValueError("unsupported ack status")
        self.status_by_command[ack.command_id]=ack.status
        self.ack_by_command[ack.command_id]=ack

    def command_status(self,command_id:str)->str:
        if command_id not in self.status_by_command:
            raise KeyError(command_id)
        return self.status_by_command[command_id]
