from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict

@dataclass
class EngineDispatcher:
    handlers:Dict[str,Callable[[dict,dict],dict]]=field(default_factory=dict)

    def register(self,engine_id:str,handler:Callable[[dict,dict],dict])->None:
        engine_id=str(engine_id).strip()
        if not engine_id or not callable(handler):
            raise ValueError("engine_id and callable handler required")
        if engine_id in self.handlers:
            raise ValueError("duplicate engine dispatcher handler")
        self.handlers[engine_id]=handler

    def execute(self,command:dict,routed:dict)->dict:
        engine_id=str(routed.get("engine_id","")).strip()
        if not engine_id:
            raise ValueError("routed engine_id required")
        handler=self.handlers.get(engine_id)
        if handler is None:
            return {
              "status":"BLOCKED",
              "reason":"ENGINE_HANDLER_NOT_REGISTERED",
              "company_id":command.get("company_id"),
              "environment":command.get("environment"),
              "version":command.get("version"),
              "engine_id":engine_id,
            }
        result=handler(dict(command),dict(routed))
        if not isinstance(result,dict) or "status" not in result:
            raise ValueError("dispatcher handler must return status-bearing dict")
        return result
