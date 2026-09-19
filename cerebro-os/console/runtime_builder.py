from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from .pipeline import ConsolePipeline
    from .http_surface import ConsoleHttpSurface
    from .engine_dispatch import EngineDispatcher
    from .onboarding_engine import OnboardingQueueEngine
    from .ui_engines import classify_command
    from .persistent_store import ConsoleStore
except ImportError:
    from pipeline import ConsolePipeline
    from http_surface import ConsoleHttpSurface
    from engine_dispatch import EngineDispatcher
    from onboarding_engine import OnboardingQueueEngine
    from ui_engines import classify_command
    from persistent_store import ConsoleStore

from runtime.onboarding_queue import OnboardingQueue
from jobs.build_onboarding_worker_health import evaluate_worker_health

@dataclass
class ConsoleRuntime:
    surface:ConsoleHttpSurface
    queue:OnboardingQueue
    audits:list[dict]
    dispatcher:EngineDispatcher
    store:ConsoleStore

def build_console_runtime(
    *,
    queue_path:str|Path,
    now_epoch_provider:Callable[[],int],
    company_reader:Callable[[],tuple[dict,...]]|None=None,
    context_reader=None,
    engine_reader=None,
    history_reader=None,
    access_reader=None,
    store_path:str|Path|None=None,
)->ConsoleRuntime:
    if not callable(now_epoch_provider):
        raise ValueError("now_epoch_provider must be callable")
    queue_path=Path(queue_path)
    queue=OnboardingQueue(queue_path)
    store=ConsoleStore(store_path or queue_path.with_name("console.sqlite3"))
    audits:list[dict]=[]
    dispatcher=EngineDispatcher()
    onboarding=OnboardingQueueEngine(queue,now_epoch_provider)
    dispatcher.register("COMP-ONB-001",onboarding.execute)

    def gateway(command:dict)->dict:
        status,intent=classify_command(str(command.get("message","")))
        if status!="GREEN":
            return {
              "status":"HUMAN_REQUIRED","reason":"LOW_CONFIDENCE",
              "company_id":command.get("company_id"),"environment":command.get("environment"),"version":command.get("version"),
            }
        if intent=="CREATE_COMPANY":
            return {
              "status":"ROUTED","company_id":command["company_id"],
              "environment":command["environment"],"version":command["version"],
              "engine_id":"COMP-ONB-001","intent":intent,
            }
        return {
          "status":"HUMAN_REQUIRED","reason":"LOW_CONFIDENCE",
          "company_id":command.get("company_id"),"environment":command.get("environment"),"version":command.get("version"),
          "intent":intent,
        }

    def audit_sink(row:dict)->None:
        audits.append(dict(row))
        store.record(dict(row),now_epoch=int(now_epoch_provider()))

    pipeline=ConsolePipeline(gateway,audit_sink,dispatcher.execute)

    def onboarding_reader()->dict:
        return evaluate_worker_health(queue=queue,now_epoch=int(now_epoch_provider()))

    def onboarding_company_reader(company_id:str)->tuple[dict,...]:
        rows=[]
        for item in queue.by_company(company_id):
            result=item.last_result or {}
            state=result.get("state") if isinstance(result,dict) else {}
            if not isinstance(state,dict):
                state={}
            prefill=result.get("remote_prefill") if isinstance(result,dict) else {}
            if not isinstance(prefill,dict):
                prefill={}
            rows.append({
              "company_id":item.company_id,
              "request_id":item.request_id,
              "status":item.status,
              "attempts":item.attempts,
              "priority":item.priority,
              "next_attempt_epoch":item.next_attempt_epoch,
              "dead_letter_reason":item.dead_letter_reason,
              "current_phase":state.get("current_phase"),
              "human_reason":result.get("human_reason") if isinstance(result,dict) else None,
              "stop_reason":result.get("stop_reason") or result.get("executor_stop_reason") if isinstance(result,dict) else None,
              "remote_prefill_green":prefill.get("green_engine_count"),
              "environment":str(item.payload.get("environment","LAB")),
              "version":item.version,
            })
        return tuple(rows)

    surface=ConsoleHttpSurface(
        pipeline,
        company_reader or (lambda: ()),
        context_reader=context_reader,
        engine_reader=engine_reader,
        history_reader=history_reader or store.history_by_company,
        audit_reader=store.audit_by_company,
        access_reader=access_reader,
        onboarding_reader=onboarding_reader,
        onboarding_company_reader=onboarding_company_reader,
    )
    return ConsoleRuntime(surface=surface,queue=queue,audits=audits,dispatcher=dispatcher,store=store)
