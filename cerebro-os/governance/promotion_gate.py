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

EVIDENCE_REQUIRED_ENVIRONMENTS = {"PREPROD", "PROD"}


def decide_promotion(
    *,
    engine_id: str,
    environment: str,
    gates: dict[str, bool],
    policy_decision: str = "ALLOW",
    human_required: bool = False,
    evidence_refs: dict[str, str] | None = None,
) -> dict:
    if not engine_id:
        raise ValueError("engine_id required")
    if environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")

    missing = tuple(gate for gate in REQUIRED_GATES if not gates.get(gate, False))
    evidence_refs = evidence_refs or {}
    missing_evidence = (
        tuple(gate for gate in REQUIRED_GATES if not str(evidence_refs.get(gate, "")).strip())
        if environment in EVIDENCE_REQUIRED_ENVIRONMENTS
        else ()
    )

    if human_required:
        return {
            "decision": "HUMAN_REQUIRED",
            "missing": missing,
            "missing_evidence": missing_evidence,
            "reason": "HUMAN_EXCEPTION",
        }
    if policy_decision == "DENY":
        return {
            "decision": "BLOCKED",
            "missing": missing,
            "missing_evidence": missing_evidence,
            "reason": "POLICY_DENY",
        }
    if policy_decision != "ALLOW":
        return {
            "decision": "HUMAN_REQUIRED",
            "missing": missing,
            "missing_evidence": missing_evidence,
            "reason": "POLICY_CONFLICT",
        }
    if missing:
        return {
            "decision": "BLOCKED",
            "missing": missing,
            "missing_evidence": missing_evidence,
            "reason": "GATES_INCOMPLETE",
        }
    if missing_evidence:
        return {
            "decision": "BLOCKED",
            "missing": (),
            "missing_evidence": missing_evidence,
            "reason": "EVIDENCE_INCOMPLETE",
        }

    target = {"LAB": "LAB_GREEN", "PREPROD": "PREPROD_GREEN", "PROD": "PROD_CANDIDATE"}[environment]
    return {"decision": target, "missing": (), "missing_evidence": (), "reason": "ALL_GATES_GREEN"}


def all_green_gates() -> dict[str, bool]:
    return {gate: True for gate in REQUIRED_GATES}


def evidence_for_all_gates(prefix: str = "evidence") -> dict[str, str]:
    """Test/helper constructor; callers must replace refs with real evidence in live promotion."""
    return {gate: f"{prefix}:{gate}" for gate in REQUIRED_GATES}
