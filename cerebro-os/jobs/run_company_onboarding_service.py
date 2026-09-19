from __future__ import annotations

import os
import time
from pathlib import Path

from runtime.onboarding_queue import OnboardingQueue
from runtime.onboarding_worker_service import WorkerServicePolicy,run_service_cycles

def run()->dict:
    db=Path(os.environ.get("CEREBRO_ONBOARD_QUEUE_DB",".cerebro-runtime/onboarding-worker/queue.sqlite3"))
    heartbeat=Path(os.environ.get("CEREBRO_ONBOARD_SERVICE_HEARTBEAT",".cerebro-runtime/onboarding-worker/service-heartbeat.json"))
    db.parent.mkdir(parents=True,exist_ok=True)
    policy=WorkerServicePolicy(
      batch_size=int(os.environ.get("CEREBRO_ONBOARD_BATCH_SIZE","25")),
      lease_seconds=int(os.environ.get("CEREBRO_ONBOARD_LEASE_SECONDS","300")),
      max_attempts=int(os.environ.get("CEREBRO_ONBOARD_MAX_ATTEMPTS","3")),
      base_backoff_seconds=int(os.environ.get("CEREBRO_ONBOARD_BASE_BACKOFF_SECONDS","60")),
      max_backoff_seconds=int(os.environ.get("CEREBRO_ONBOARD_MAX_BACKOFF_SECONDS","3600")),
      min_sleep_seconds=int(os.environ.get("CEREBRO_ONBOARD_MIN_SLEEP_SECONDS","5")),
      max_idle_sleep_seconds=int(os.environ.get("CEREBRO_ONBOARD_MAX_IDLE_SLEEP_SECONDS","60")),
    )
    return run_service_cycles(
      queue=OnboardingQueue(db),
      now_epoch_provider=lambda:int(time.time()),
      sleep=time.sleep,
      policy=policy,
      max_cycles=int(os.environ.get("CEREBRO_ONBOARD_SERVICE_MAX_CYCLES","1")),
      heartbeat_path=heartbeat,
    )

if __name__=="__main__":
    print(run())
