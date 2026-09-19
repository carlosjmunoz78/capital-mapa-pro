from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from jobs.company_onboarding_orchestrator import PHASE_ENGINE_MAP, default_phase_plan
from jobs.company_onboarding_superloop import run_superloop

SAFE_EXECUTION_MODES={"LOCAL_DETERMINISTIC","READ_ONLY","PREPROD_ONLY","GATE_ONLY"}

@dataclass(frozen=True)
class EngineHandler:
    engine_id:str
    handler:Callable[[dict],dict]
    execution_modes:tuple[str,...]=("LOCAL_DETERMINISTIC",)
    external_mutation_allowed:bool=False
    cost_eur:float=0.0

    def validate(self)->None:
        if not self.engine_id.strip() or not callable(self.handler):
            raise ValueError("valid engine handler required")
        if not self.execution_modes or any(x not in SAFE_EXECUTION_MODES for x in self.execution_modes):
            raise ValueError("unsupported handler execution mode")
        if self.external_mutation_allowed:
            raise ValueError("onboarding V0 handlers cannot mutate externally")
        if self.cost_eur!=0:
            raise ValueError("onboarding V0 handlers must be zero cost")

class OnboardingHandlerRegistry:
    def __init__(self):
        self._handlers:dict[str,EngineHandler]={}

    def register(self,item:EngineHandler)->None:
        item.validate()
        if item.engine_id in self._handlers:
            raise ValueError("duplicate engine handler")
        self._handlers[item.engine_id]=item

    def get(self,engine_id:str)->EngineHandler|None:
        return self._handlers.get(engine_id)

def _handler_payload(*,state:dict,plan:dict,context:dict)->dict:
    return {
      "company_id":str(state["company_id"]),
      "engine_id":str(plan["target_engine_id"]),
      "phase":str(plan["phase"]),
      "environment":str(plan["environment"]),
      "version":str(state.get("version","1.0.0")),
      "execution_mode":str(plan["execution_mode"]),
      "allowed_external_mutation":False,
      "required_cost_eur":0.0,
      "required_gates":tuple(plan.get("required_gates") or ()),
      "context":dict(context),
    }

def execute_onboarding_superloop(
    state:dict,
    *,
    registry:OnboardingHandlerRegistry,
    context:dict|None=None,
    max_steps:int=50,
)->dict:
    if max_steps<1:
        raise ValueError("max_steps must be >= 1")
    current=dict(state)
    context=dict(context or {})
    engine_results:list[dict]=[]
    executed=[]

    for _ in range(max_steps):
        if current.get("current_phase") is None:
            return run_superloop(current,engine_results,max_steps=max_steps)

        plan=default_phase_plan(current)
        mode=str(plan["execution_mode"])
        engine_id=str(plan["target_engine_id"])
        if mode not in SAFE_EXECUTION_MODES:
            raise ValueError("unsafe execution mode")
        if plan.get("allowed_external_mutation"):
            raise ValueError("external mutation is forbidden in onboarding executor V0")
        if float(plan.get("required_cost_eur",0.0))!=0.0:
            raise ValueError("non-zero onboarding execution cost is forbidden in V0")

        handler=registry.get(engine_id)
        if handler is None:
            preview=run_superloop(current,engine_results,max_steps=max_steps)
            return {
              **preview,
              "executor_stop_reason":"HANDLER_MISSING",
              "missing_handler_engine_id":engine_id,
              "executed_handlers":tuple(executed),
              "external_mutation_allowed":False,
              "cost_eur":0.0,
            }
        if mode not in handler.execution_modes:
            return {
              "company_id":current["company_id"],
              "status":"BLOCKED",
              "state":current,
              "executor_stop_reason":"HANDLER_MODE_MISMATCH",
              "handler_engine_id":engine_id,
              "required_execution_mode":mode,
              "handler_execution_modes":handler.execution_modes,
              "executed_handlers":tuple(executed),
              "external_mutation_allowed":False,
              "cost_eur":0.0,
            }

        payload=_handler_payload(state=current,plan=plan,context=context)
        result=handler.handler(payload)
        if not isinstance(result,dict):
            raise ValueError("engine handler must return object")
        if str(result.get("company_id",""))!=str(current["company_id"]):
            raise ValueError("cross-company handler result denied")
        if str(result.get("engine_id",""))!=engine_id:
            raise ValueError("handler engine_id mismatch")
        if result.get("external_mutation_performed"):
            raise ValueError("handler reported forbidden external mutation")
        if float(result.get("cost_eur",0.0))!=0.0:
            raise ValueError("handler reported non-zero cost")

        engine_results.append(result)
        executed.append({
          "phase":plan["phase"],"engine_id":engine_id,"execution_mode":mode,
          "status":str(result.get("status","UNKNOWN")).upper(),
          "evidence_ref":str(result.get("evidence_hash") or result.get("evidence_ref") or ""),
        })

        loop=run_superloop(current,[result],max_steps=2)
        current=dict(loop["state"])
        if loop["status"]=="BLOCKED":
            return {
              **loop,
              "executor_stop_reason":loop["stop_reason"],
              "executed_handlers":tuple(executed),
              "external_mutation_allowed":False,
              "cost_eur":0.0,
            }
        if loop["status"]=="HUMAN_REQUIRED":
            return {
              **loop,
              "executor_stop_reason":loop["stop_reason"],
              "executed_handlers":tuple(executed),
              "external_mutation_allowed":False,
              "cost_eur":0.0,
            }
        if loop["status"]=="WAITING" and loop.get("stop_reason")=="ENGINE_RESULT_MISSING":
            continue
        if loop["status"]=="WAITING" and loop.get("stop_reason")=="ENGINE_NOT_GREEN":
            return {
              **loop,
              "executor_stop_reason":"ENGINE_NOT_GREEN",
              "executed_handlers":tuple(executed),
              "external_mutation_allowed":False,
              "cost_eur":0.0,
            }

    return {
      "company_id":current["company_id"],"status":"BLOCKED","state":current,
      "executor_stop_reason":"MAX_STEPS_REACHED","executed_handlers":tuple(executed),
      "external_mutation_allowed":False,"cost_eur":0.0,
    }
