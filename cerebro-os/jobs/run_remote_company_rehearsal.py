from __future__ import annotations

from pathlib import Path
from typing import Callable

from console.runtime_builder import build_console_runtime
from jobs.run_company_onboarding_worker import process_batch

def run_remote_company_rehearsal(
    *,
    company_id:str,
    version:str,
    context:dict,
    workdir:str|Path,
    now_epoch_provider:Callable[[],int],
)->dict:
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id/version required")
    if not isinstance(context,dict):
        raise ValueError("context must be object")
    if not callable(now_epoch_provider):
        raise ValueError("now_epoch_provider must be callable")
    if str(context.get("company_id",company_id))!=company_id:
        raise ValueError("cross-company rehearsal context denied")

    root=Path(workdir)
    root.mkdir(parents=True,exist_ok=True)
    queue_path=root/"onboarding.sqlite3"
    request_id=f"remote-rehearsal-{company_id}"

    def loader(cid,context_id,command):
        if cid!=company_id:
            raise ValueError("cross-company context loader denied")
        return {**context,"company_id":company_id}

    runtime=build_console_runtime(
        queue_path=queue_path,
        store_path=root/"console.sqlite3",
        now_epoch_provider=now_epoch_provider,
        company_reader=lambda:({"company_id":company_id,"name":company_id,"status":"REHEARSAL"},),
        onboarding_context_loader=loader,
    )
    submitted=runtime.surface.handle(
        method="POST",path="/commands",user_id="REHEARSAL",
        payload={
          "request_id":request_id,"company_id":company_id,"context_type":"company",
          "context_id":f"company:{company_id}","message":"crear empresa",
          "environment":"LAB","version":version,
        },
    )
    if submitted.status!=200:
        raise RuntimeError("rehearsal console submission failed")

    worker=process_batch(
        queue=runtime.queue,now_epoch=int(now_epoch_provider())+1,
        max_items=1,lease_seconds=30,max_attempts=2,
        base_backoff_seconds=5,max_backoff_seconds=30,
    )
    item=runtime.queue.get(request_id)
    if item is None or not isinstance(item.last_result,dict):
        raise RuntimeError("rehearsal did not persist onboarding result")

    remote=runtime.surface.handle(
        method="GET",path=f"/onboarding/remote/{company_id}",user_id="REHEARSAL"
    )
    company_view=runtime.surface.handle(
        method="GET",path=f"/onboarding/company/{company_id}",user_id="REHEARSAL"
    )
    if remote.status!=200 or company_view.status!=200:
        raise RuntimeError("rehearsal console status read failed")

    remote_rows=tuple(remote.body.get("items") or ())
    latest_remote=remote_rows[0] if remote_rows else {}
    last=item.last_result
    prefill=last.get("remote_prefill") or {}
    return {
      "record_type":"remote_company_onboarding_rehearsal",
      "company_id":company_id,
      "engine_id":"ONB-RMT-E2E-001",
      "environment":"LAB",
      "version":version,
      "status":"GREEN" if item.status in {"WAITING","COMPLETED"} else item.status,
      "queue_status":item.status,
      "worker_status":worker.get("status"),
      "current_phase":(last.get("state") or {}).get("current_phase"),
      "remote_prefill_green_count":int(prefill.get("green_engine_count",0) or 0),
      "remote_prefill_engine_count":int(prefill.get("engine_count",0) or 0),
      "remote_gap_classification":latest_remote.get("classification"),
      "remotely_actionable":latest_remote.get("remotely_actionable"),
      "local_pc_required":latest_remote.get("local_pc_required"),
      "next_action":latest_remote.get("next_action"),
      "console_audit_count":runtime.store.counts()["audit"],
      "console_history_count":runtime.store.counts()["history"],
      "external_mutation_performed":False,
      "production_activation_allowed":False,
      "computer_use_performed":False,
      "browser_bridge_used":False,
      "cost_eur":0.0,
    }
