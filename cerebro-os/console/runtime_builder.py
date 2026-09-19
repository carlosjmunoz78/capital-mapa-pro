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
except ImportError:
    from pipeline import ConsolePipeline
    from http_surface import ConsoleHttpSurface
    from engine_dispatch import EngineDispatcher
    from onboarding_engine import OnboardingQueueEngine
    from ui_engines import classify_command

from runtime.onboarding_queue import OnboardingQueue
from jobs.build_onboarding_worker_health import evaluate_worker_health

@dataclass
class ConsoleRuntime:
    surface:ConsoleHttpSurface
    queue:OnboardingQueue
    audits:list[dict]
    dispatcher:EngineDispatcher

def build_console_runtime(
    *,
    queue_path:str|Path,
    now_epoch_provider:Callable[[],int],
    company_reader:Callable[[],tuple[dict,...]]|None=None,
    context_reader=None,
    engine_reader=None,
    history_reader=None,
    access_reader=None,
)->ConsoleRuntime:
    if not callable(now_epoch_provider):
        raise ValueError("now_epoch_provider must be callable")
    queue=OnboardingQueue(queue_path)
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

    pipeline=ConsolePipeline(gateway,audits.append,dispatcher.execute)

    def onboarding_reader()->dict:
        return evaluate_worker_health(queue=queue,now_epoch=int(now_epoch_provider()))

    surface=ConsoleHttpSurface(
        pipeline,
        company_reader or (lambda: ()),
        context_reader=context_reader,
        engine_reader=engine_reader,
        history_reader=history_reader,
        audit_reader=lambda company_id: tuple(x for x in audits if x.get("company_id")==company_id),
        access_reader=access_reader,
        onboarding_reader=onboarding_reader,
    )
    return ConsoleRuntime(surface=surface,queue=queue,audits=audits,dispatcher=dispatcher)
