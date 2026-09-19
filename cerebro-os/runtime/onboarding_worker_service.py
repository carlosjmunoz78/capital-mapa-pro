from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jobs.run_company_onboarding_worker import process_batch
from runtime.onboarding_queue import OnboardingQueue

@dataclass(frozen=True)
class WorkerServicePolicy:
    batch_size:int=25
    lease_seconds:int=300
    max_attempts:int=3
    base_backoff_seconds:int=60
    max_backoff_seconds:int=3600
    min_sleep_seconds:int=5
    max_idle_sleep_seconds:int=60

    def validate(self)->None:
        if self.batch_size<1 or self.lease_seconds<1 or self.max_attempts<1:
            raise ValueError("invalid worker service policy")
        if self.base_backoff_seconds<1 or self.max_backoff_seconds<self.base_backoff_seconds:
            raise ValueError("invalid retry backoff policy")
        if self.min_sleep_seconds<1 or self.max_idle_sleep_seconds<self.min_sleep_seconds:
            raise ValueError("invalid service sleep policy")

def _safe_heartbeat(*,cycle:int,now_epoch:int,batch:dict,next_due_epoch:int|None)->dict:
    stats=dict(batch.get("queue_stats") or {})
    return {
      "record_type":"onboarding_worker_service_heartbeat",
      "company_id":"GLOBAL",
      "engine_id":"ONB-SVC-HLT-001",
      "environment":"LAB",
      "version":"1.0.0",
      "cycle":cycle,
      "observed_at_epoch":now_epoch,
      "status":batch.get("status","GREEN"),
      "processed_count":int(batch.get("processed_count",0)),
      "human_required_count":int(batch.get("human_required_count",0)),
      "blocked_count":int(batch.get("blocked_count",0)),
      "retry_scheduled_count":int(batch.get("retry_scheduled_count",0)),
      "queue_stats":stats,
      "next_due_epoch":next_due_epoch,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "raw_secret_storage_allowed":False,
      "cost_eur":0.0,
    }

def run_service_cycles(
    *,
    queue:OnboardingQueue,
    now_epoch_provider:Callable[[],int],
    sleep:Callable[[int],None],
    policy:WorkerServicePolicy|None=None,
    max_cycles:int=1,
    heartbeat_path:str|Path|None=None,
)->dict:
    if not isinstance(queue,OnboardingQueue):
        raise ValueError("OnboardingQueue required")
    if not callable(now_epoch_provider) or not callable(sleep):
        raise ValueError("time providers must be callable")
    if max_cycles<0:
        raise ValueError("max_cycles must be >= 0")
    policy=policy or WorkerServicePolicy()
    policy.validate()
    heartbeat_target=Path(heartbeat_path) if heartbeat_path is not None else None
    if heartbeat_target is not None:
        heartbeat_target.parent.mkdir(parents=True,exist_ok=True)

    cycles=[]
    cycle=0
    while max_cycles==0 or cycle<max_cycles:
        cycle+=1
        now=int(now_epoch_provider())
        if now<0:
            raise ValueError("invalid service timestamp")
        batch=process_batch(
            queue=queue,now_epoch=now,max_items=policy.batch_size,lease_seconds=policy.lease_seconds,
            max_attempts=policy.max_attempts,base_backoff_seconds=policy.base_backoff_seconds,
            max_backoff_seconds=policy.max_backoff_seconds,
        )
        next_due=queue.next_due_epoch(now_epoch=now)
        heartbeat=_safe_heartbeat(cycle=cycle,now_epoch=now,batch=batch,next_due_epoch=next_due)
        if heartbeat_target is not None:
            heartbeat_target.write_text(json.dumps(heartbeat,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        cycles.append(heartbeat)

        if max_cycles!=0 and cycle>=max_cycles:
            break

        if next_due is None:
            wait=policy.max_idle_sleep_seconds
        else:
            wait=max(policy.min_sleep_seconds,min(policy.max_idle_sleep_seconds,max(0,next_due-now)))
        sleep(int(wait))

    last=cycles[-1] if cycles else {}
    return {
      "record_type":"onboarding_worker_service_run",
      "company_id":"GLOBAL",
      "engine_id":"ONB-SVC-001",
      "environment":"LAB",
      "version":"1.0.0",
      "cycles":tuple(cycles),
      "cycle_count":len(cycles),
      "last_status":last.get("status","GREEN"),
      "continuous_mode_supported":True,
      "max_cycles":max_cycles,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }
