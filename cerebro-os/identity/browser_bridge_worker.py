from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from browser_bridge_protocol import BridgeAck,BridgeCommandQueue
from browser_bridge_result_policy import evaluate_bridge_result

@dataclass(frozen=True)
class WorkerIdentity:
    company_id:str
    device_id:str
    environment:str
    version:str

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.company_id,self.device_id,self.environment,self.version)):
            raise ValueError("worker identity scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid worker environment")

def execute_one(
    *,
    worker:WorkerIdentity,
    queue:BridgeCommandQueue,
    executor:Callable[[dict],dict],
    now_epoch:int,
)->dict:
    worker.validate()
    if not callable(executor):
        raise ValueError("executor must be callable")
    if worker.environment=="PROD":
        return {
          "status":"HUMAN_REQUIRED","decision":"PROD_WORKER_DISABLED_V0",
          "human_reason":"HIGH_RISK","claimed":False,"executed":False,"cost_eur":0.0,
        }

    command=queue.claim(
        company_id=worker.company_id,device_id=worker.device_id,
        environment=worker.environment,version=worker.version,now_epoch=now_epoch,
    )
    if command is None:
        return {
          "status":"GREEN","decision":"NO_COMMAND","human_reason":None,
          "claimed":False,"executed":False,"cost_eur":0.0,
        }

    safe_payload={
        "command_id":command.command_id,
        "request_id":command.request_id,
        "company_id":command.company_id,
        "identity_id":command.identity_id,
        "account_id":command.account_id,
        "engine_id":command.engine_id,
        "capability":command.capability,
        "action":command.action,
        "device_id":command.device_id,
        "profile_id":command.profile_id,
        "environment":command.environment,
        "version":command.version,
        "idempotency_key":command.idempotency_key,
        "audit_ref":command.audit_ref,
    }

    try:
        result=executor(safe_payload)
    except Exception:
        result={"status":"FAILED","evidence_ref":"","side_effect_reported":False}

    if not isinstance(result,dict):
        result={"status":"FAILED","evidence_ref":"","side_effect_reported":False}

    raw_status=str(result.get("status","FAILED")).upper()
    ack_status=raw_status if raw_status in {"ACKNOWLEDGED","IN_PROGRESS","COMPLETED","FAILED","CANCELLED"} else "FAILED"
    evidence_ref=str(result.get("evidence_ref","")).strip()

    queue.acknowledge(BridgeAck(
        command_id=command.command_id,request_id=command.request_id,
        idempotency_key=command.idempotency_key,device_id=command.device_id,
        company_id=command.company_id,environment=command.environment,version=command.version,
        status=ack_status,observed_at_epoch=now_epoch,evidence_ref=evidence_ref,
    ))

    expected_side_effect=bool(result.get("expected_side_effect",True))
    side_effect_reported=bool(result.get("side_effect_reported",False))
    policy=evaluate_bridge_result(
        command_status=ack_status,evidence_ref=evidence_ref,
        side_effect_reported=side_effect_reported,expected_side_effect=expected_side_effect,
    )
    return {
      "status":policy["status"],"decision":policy["decision"],
      "human_reason":policy.get("human_reason"),"claimed":True,"executed":True,
      "command_id":command.command_id,"request_id":command.request_id,
      "queue_status":queue.command_status(command.command_id),
      "evidence_ref":evidence_ref,"promotion_allowed":policy["promotion_allowed"],
      "executor_payload_contains_secret":False,"executor_payload_contains_credential_value":False,
      "cost_eur":0.0,
    }
