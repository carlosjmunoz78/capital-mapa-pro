from __future__ import annotations

import json
from pathlib import Path

REQUIRED = {9533982,9534003,9534002,9533999,9533998}


def load_fixture(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_factory_adapters(data: dict) -> dict:
    adapters = data.get("adapters") or []
    by_id = {int(item["scenario_id"]): item for item in adapters}
    failures: list[str] = []

    missing = sorted(REQUIRED - set(by_id))
    if missing:
        failures.append("missing:" + ",".join(map(str, missing)))
    if data.get("folder_id") != 520864:
        failures.append("wrong_folder")
    if data.get("data_store_id") != 171764:
        failures.append("wrong_datastore")

    for sid in REQUIRED & set(by_id):
        item = by_id[sid]
        if item.get("status") != "inactive":
            failures.append(f"{sid}:must_remain_inactive")
        if item.get("external_action_allowed") is not False:
            failures.append(f"{sid}:external_action_not_fail_closed")
        if not str(item.get("operation") or "").strip():
            failures.append(f"{sid}:missing_operation")
        if not str(item.get("provider_state") or "").startswith(("BLOCKED_", "QUEUED_")):
            failures.append(f"{sid}:provider_state_not_blocked")

    policy = data.get("policy") or {}
    required_policy = {
        "preserve_legacy": True,
        "auto_activate_allowed": False,
        "paid_provider_required": False,
        "paid_ai_required": False,
        "external_action_allowed": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            failures.append(f"policy:{key}")
    if policy.get("migration_target") != "ENGINE_FACTORY_SHARED_RUNTIME":
        failures.append("policy:migration_target")

    return {
        "status": "GREEN_CODE_CI" if not failures else "RED",
        "adapter_count": len(REQUIRED & set(by_id)),
        "failures": tuple(failures),
        "preserve_legacy": True,
        "external_action_allowed": False,
        "additional_cost_required": False,
    }
