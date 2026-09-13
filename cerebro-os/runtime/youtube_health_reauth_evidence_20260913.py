from __future__ import annotations

EVIDENCE = {
    "scenario_id": 9537666,
    "scenario_name": "FENIX · HEALTH · YouTube · Canal, vídeos y permisos · V1",
    "previous_execution_error": "Failed to verify connection; HTTP 400",
    "previous_operations": 0,
    "reauthorization_completed": True,
    "new_connection_id": 14591497,
    "new_connection_scope": "youtube",
    "modules_rewired": (1, 2),
    "scenario_temporarily_activated": True,
    "manual_run_attempted": True,
    "manual_run_executed": False,
    "manual_run_blocked_by_execution_controls": True,
    "scenario_left_active": False,
    "retained_success_execution_proven": False,
}


def assess() -> dict:
    return {
        "youtube_reauthorization_green": EVIDENCE["reauthorization_completed"],
        "youtube_connection_rewired_green": len(EVIDENCE["modules_rewired"]) == 2,
        "youtube_health_retained_metric_green": EVIDENCE["retained_success_execution_proven"],
        "safe_final_state_inactive": EVIDENCE["scenario_left_active"] is False,
        "automatic_prod_publication_permitted": False,
        "status": "YOUTUBE_REAUTHORIZED_REWIRED_MANUAL_EXECUTION_TOOL_BLOCKED_FAIL_CLOSED",
    }
