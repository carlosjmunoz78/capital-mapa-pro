from __future__ import annotations

REQUIRED_GATES = (
    "contracts",
    "permissions",
    "tests",
    "evaluation",
    "tribunal",
    "observability",
    "rollback",
    "backup",
    "rebuild",
    "cost",
    "policy",
    "tenant_isolation",
)


def decide_promotion(*, engine_id: str, environment: str, gates: dict[str, bool], policy_decision: str = "ALLOW", human_required: bool = False) -> dict:
    if not engine_id:
        raise ValueError("engine_id required")
    if environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")
    missing = tuple(gate for gate in REQUIRED_GATES if not gates.get(gate, False))
    if human_required:
        return {"decision": "HUMAN_REQUIRED", "missing": missing, "reason": "HUMAN_EXCEPTION"}
    if policy_decision == "DENY":
        return {"decision": "BLOCKED", "missing": missing, "reason": "POLICY_DENY"}
    if policy_decision != "ALLOW":
        return {"decision": "HUMAN_REQUIRED", "missing": missing, "reason": "POLICY_CONFLICT"}
    if missing:
        return {"decision": "BLOCKED", "missing": missing, "reason": "GATES_INCOMPLETE"}
    target = {"LAB": "LAB_GREEN", "PREPROD": "PREPROD_GREEN", "PROD": "PROD_CANDIDATE"}[environment]
    return {"decision": target, "missing": (), "reason": "ALL_GATES_GREEN"}


def all_green_gates() -> dict[str, bool]:
    return {gate: True for gate in REQUIRED_GATES}
