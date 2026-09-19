from __future__ import annotations

import os
import time
from pathlib import Path

from runtime.onboarding_queue import OnboardingQueue
from jobs.run_company_onboarding_executor import run_request

def process_one(*,queue:OnboardingQueue,now_epoch:int,lease_seconds:int=300)->dict:
    item=queue.claim(now_epoch=now_epoch,lease_seconds=lease_seconds)
    if item is None:
        return {"status":"GREEN","decision":"NO_WORK","processed":False,"cost_eur":0.0}

    try:
        result=run_request(item.payload,item.last_result)
        state=str(result.get("status","BLOCKED")).upper()
        mapped={
          "WAITING":"WAITING",
          "BLOCKED":"BLOCKED",
          "HUMAN_REQUIRED":"HUMAN_REQUIRED",
          "GREEN":"COMPLETED",
        }.get(state,"BLOCKED")
    except Exception as exc:
        result={
          "record_type":"company_onboarding_worker_failure",
          "company_id":item.company_id,
          "version":item.version,
          "status":"BLOCKED",
          "reason":"EXECUTOR_EXCEPTION",
          "error_type":type(exc).__name__,
          "external_mutation_allowed":False,
          "production_activation_allowed":False,
          "cost_eur":0.0,
        }
        mapped="BLOCKED"

    queue.complete(request_id=item.request_id,status=mapped,result=result,now_epoch=now_epoch)
    return {
      "status":mapped,
      "decision":"PROCESSED",
      "processed":True,
      "request_id":item.request_id,
      "company_id":item.company_id,
      "attempts":item.attempts,
      "executor_status":str(result.get("status","BLOCKED")).upper(),
      "human_reason":result.get("human_reason"),
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }

def run()->dict:
    db=Path(os.environ.get("CEREBRO_ONBOARD_QUEUE_DB",".cerebro-runtime/onboarding-worker/queue.sqlite3"))
    db.parent.mkdir(parents=True,exist_ok=True)
    queue=OnboardingQueue(db)
    return process_one(queue=queue,now_epoch=int(time.time()),lease_seconds=int(os.environ.get("CEREBRO_ONBOARD_LEASE_SECONDS","300")))

if __name__=="__main__":
    print(run())
