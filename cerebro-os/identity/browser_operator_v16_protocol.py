"""Protocol contract for Browser Operator v1.6 LAB physical acceptance.
Pure deterministic validation; no browser execution.
"""
from __future__ import annotations
from dataclasses import dataclass

ACTIONS={"OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"}
SELECTORS={
 "OPERATOR_CLICK":{"#cerebro-button"},
 "OPERATOR_TYPE":{"#cerebro-input"},
 "OPERATOR_SELECT":{"#cerebro-select"},
 "OPERATOR_READ":{"#cerebro-output"},
}

@dataclass(frozen=True)
class OperatorCommand:
 command_id:str; company_id:str; environment:str; version:str
 action:str; target_url:str; selector:str; value:str=""

def validate(cmd:OperatorCommand, port:int)->dict:
 blockers=[]
 expected=f"http://127.0.0.1:{port}/lab/operator-fixture"
 if cmd.company_id!="fenix" or cmd.environment!="LAB" or cmd.version!="v0": blockers.append("SCOPE_DENIED")
 if cmd.action not in ACTIONS: blockers.append("ACTION_DENIED")
 if cmd.target_url!=expected: blockers.append("TARGET_DENIED")
 if cmd.selector not in SELECTORS.get(cmd.action,set()): blockers.append("SELECTOR_DENIED")
 if cmd.action=="OPERATOR_TYPE" and (not isinstance(cmd.value,str) or len(cmd.value)>64): blockers.append("VALUE_DENIED")
 if cmd.action=="OPERATOR_SELECT" and cmd.value not in {"alpha","beta"}: blockers.append("VALUE_DENIED")
 if cmd.action in {"OPERATOR_CLICK","OPERATOR_READ"} and cmd.value: blockers.append("VALUE_DENIED")
 return {"status":"GREEN" if not blockers else "BLOCKED","blockers":tuple(blockers),
 "external_mutation_allowed":False,"prod_activation_allowed":False,"secret_value_allowed":False,
 "target_url":expected if not blockers else None,"cost_eur":0.0}

def verify_receipt(action:str,status:str,evidence:str,observed_value:str)->bool:
 if action not in ACTIONS or status!="COMPLETED" or evidence!="LAB_OPERATOR_FIXTURE_VERIFIED": return False
 if not isinstance(observed_value,str) or len(observed_value)>64:return False
 if action=="OPERATOR_CLICK":return observed_value=="CLICKED"
 if action=="OPERATOR_SELECT":return observed_value in {"alpha","beta"}
 if action=="OPERATOR_TYPE":return len(observed_value)>0
 if action=="OPERATOR_READ":return observed_value in {"READY","CLICKED"}
 return False
