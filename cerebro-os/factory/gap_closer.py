from __future__ import annotations

STANDARD_REQUIREMENTS = (
    "manifest",
    "config",
    "contracts",
    "permissions",
    "policies",
    "events",
    "jobs",
    "api",
    "tests",
    "evaluation",
    "tribunal",
    "observability",
    "cost",
    "backup",
    "rollback",
    "rebuild",
    "docs",
    "training_hooks",
)

AUTO_SAFE = {
    "manifest", "config", "contracts", "events", "jobs", "api", "tests",
    "evaluation", "observability", "cost", "backup", "rollback", "rebuild", "docs", "training_hooks",
}


def gap_actions(engine_id: str, present: set[str] | tuple[str, ...] | list[str]) -> dict:
    if not engine_id:
        raise ValueError("engine_id required")
    present_set = set(present)
    unknown = present_set - set(STANDARD_REQUIREMENTS)
    if unknown:
        raise ValueError(f"unknown requirement markers: {sorted(unknown)}")
    missing = tuple(item for item in STANDARD_REQUIREMENTS if item not in present_set)
    actions = []
    for requirement in missing:
        mode = "SAFE_AUTOFIX" if requirement in AUTO_SAFE else "POLICY_REVIEW"
        actions.append({
            "engine_id": engine_id,
            "requirement": requirement,
            "mode": mode,
            "action": f"ensure_{requirement}",
        })
    return {
        "engine_id": engine_id,
        "complete": not missing,
        "missing": missing,
        "actions": tuple(actions),
    }
