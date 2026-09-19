from __future__ import annotations

SUCCESS_STATUSES={"COMPLETED"}
FAILURE_STATUSES={"FAILED","CANCELLED","EXPIRED"}

def evaluate_bridge_result(*,command_status:str,evidence_ref:str,side_effect_reported:bool,expected_side_effect:bool)->dict:
    status=str(command_status).upper().strip()
    evidence=str(evidence_ref).strip()
    if status in SUCCESS_STATUSES:
        if not evidence:
            return {
              "status":"BLOCKED","decision":"COMPLETION_EVIDENCE_REQUIRED",
              "promotion_allowed":False,"human_reason":None,
            }
        if expected_side_effect and not side_effect_reported:
            return {
              "status":"BLOCKED","decision":"EXPECTED_SIDE_EFFECT_NOT_CONFIRMED",
              "promotion_allowed":False,"human_reason":None,
            }
        if not expected_side_effect and side_effect_reported:
            return {
              "status":"HUMAN_REQUIRED","decision":"UNEXPECTED_SIDE_EFFECT_REPORTED",
              "promotion_allowed":False,"human_reason":"SECURITY_INCIDENT",
            }
        return {
          "status":"GREEN","decision":"COMMAND_EVIDENCE_ACCEPTED",
          "promotion_allowed":True,"human_reason":None,
        }
    if status in FAILURE_STATUSES:
        return {
          "status":"BLOCKED","decision":"COMMAND_NOT_SUCCESSFUL",
          "promotion_allowed":False,"human_reason":None,
        }
    return {
      "status":"WAITING","decision":"COMMAND_STILL_ACTIVE",
      "promotion_allowed":False,"human_reason":None,
    }
