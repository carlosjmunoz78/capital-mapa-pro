from __future__ import annotations

import json
import os
import time
from pathlib import Path

from runtime.onboarding_queue import OnboardingQueue

ENGINE_ID="ONB-WRK-HLT-001"

def evaluate_worker_health(*,queue:OnboardingQueue,now_epoch:int)->dict:
    stats=queue.stats(now_epoch=now_epoch)
    if stats["human_required"]>0:
        status="HUMAN_REQUIRED"; human_reason="HIGH_RISK"
    elif stats["stale_leases"]>0 or stats["blocked"]>0:
        status="DEGRADED"; human_reason=None
    else:
        status="GREEN"; human_reason=None
    return {
      "record_type":"onboarding_worker_health",
      "company_id":"GLOBAL",
      "engine_id":ENGINE_ID,
      "environment":"LAB",
      "version":"1.0.0",
      "status":status,
      "human_reason":human_reason,
      "queue_stats":stats,
      "worker_autonomous":True,
      "stale_lease_reclaim_supported":True,
      "raw_secret_storage_allowed":False,
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }

def run()->Path:
    db=Path(os.environ.get("CEREBRO_ONBOARD_QUEUE_DB",".cerebro-runtime/onboarding-worker/queue.sqlite3"))
    out=Path(os.environ.get("CEREBRO_ONBOARD_WORKER_HEALTH",".cerebro-runtime/onboarding-worker/health.json"))
    out.parent.mkdir(parents=True,exist_ok=True)
    result=evaluate_worker_health(queue=OnboardingQueue(db),now_epoch=int(time.time()))
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return out

if __name__=="__main__":
    print(run())
