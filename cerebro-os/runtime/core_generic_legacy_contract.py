from __future__ import annotations

import json
from pathlib import Path

REQUIRED_SCENARIOS = {9524837, 9527140, 9527162, 9537817}


def load_fixture(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def validate_generic_core_legacy_contract(data: dict) -> dict:
    scenarios = data.get("scenarios") or []
    by_id = {int(item["scenario_id"]): item for item in scenarios}
    missing = sorted(REQUIRED_SCENARIOS - set(by_id))
    failures: list[str] = []

    if data.get("folder_id") != 520864:
        failures.append("wrong_core_folder")
    if data.get("data_store_id") != 171764:
        failures.append("wrong_datastore")
    if missing:
        failures.append(f"missing_scenarios:{','.join(map(str, missing))}")

    for scenario_id, item in by_id.items():
        if scenario_id not in REQUIRED_SCENARIOS:
            continue
        if item.get("status") != "inactive":
            failures.append(f"{scenario_id}:must_remain_inactive")
        if item.get("incomplete_executions") != 0:
            failures.append(f"{scenario_id}:incomplete_executions")
        expected = item.get("expected") or {}
        if expected.get("external_action_allowed") is not False:
            failures.append(f"{scenario_id}:external_action_not_fail_closed")
        if not str(item.get("runtime_target") or "").strip():
            failures.append(f"{scenario_id}:missing_runtime_target")

    dispatcher = by_id.get(9537817, {}).get("expected", {})
    if dispatcher:
        required_true = (
            "requires_programming_relation",
            "requires_production_order",
            "requires_t48_approved",
            "requires_t48_approval_date",
            "requires_t48_locked_version",
            "requires_t48_hash",
        )
        for key in required_true:
            if dispatcher.get(key) is not True:
                failures.append(f"9537817:{key}_not_required")
        if dispatcher.get("platform_state") != "NOT_CALLED":
            failures.append("9537817:platform_must_not_be_called")

    return {
        "status": "GREEN_CODE_CI" if not failures else "RED",
        "scenario_count": len([sid for sid in by_id if sid in REQUIRED_SCENARIOS]),
        "failures": tuple(failures),
        "old_preserved": True,
        "auto_activate_allowed": False,
        "delete_allowed": False,
        "external_action_allowed": False,
    }
