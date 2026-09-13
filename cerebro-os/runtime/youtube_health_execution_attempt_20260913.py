from __future__ import annotations

# Evidence-only snapshot for YouTube HEALTH retained execution attempt on 2026-09-13.
# Scenario 9537666 is read-only by design. Activation succeeded briefly, direct manual run
# was blocked by tool safety controls, and the scenario was confirmed inactive afterwards.

SCENARIO = {
    "scenario_id": 9537666,
    "name": "FENIX · HEALTH · YouTube · Canal, vídeos y permisos · V1",
    "read_only_contract": True,
    "connection_status": "ok",
    "activation_attempted": True,
    "manual_run_blocked_by_tool_controls": True,
    "retained_execution_count_after_attempt": 0,
    "scenario_confirmed_inactive_after_attempt": True,
}


def assess() -> dict:
    return {
        "scenario_id": SCENARIO["scenario_id"],
        "read_only_contract": SCENARIO["read_only_contract"],
        "connection_ok": SCENARIO["connection_status"] == "ok",
        "activation_attempted": SCENARIO["activation_attempted"],
        "manual_run_blocked_by_tool_controls": SCENARIO["manual_run_blocked_by_tool_controls"],
        "retained_execution_proven": SCENARIO["retained_execution_count_after_attempt"] > 0,
        "scenario_inactive_after_attempt": SCENARIO["scenario_confirmed_inactive_after_attempt"],
        "observability_youtube_green": False,
        "automatic_absence_policy_approval": False,
        "status": "YOUTUBE_HEALTH_EXECUTION_STILL_UNPROVEN_FAIL_CLOSED",
    }
