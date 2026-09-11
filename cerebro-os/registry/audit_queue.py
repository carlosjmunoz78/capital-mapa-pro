from __future__ import annotations

PRIORITY = {
    "BLOCKED": 0,
    "HUMAN_REQUIRED": 1,
    "UNKNOWN_REQUIRES_AUDIT": 2,
    "DOCUMENTED_PARTIAL": 3,
    "DEFINED_NOT_BUILT": 4,
    "LAB_GREEN": 5,
    "CONFIRMED_OPERATIONAL": 6,
}

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def build_audit_queue(matrix, *, target_environment: str = "LAB", company_id: str | None = None) -> tuple[dict, ...]:
    """Build a deterministic gap queue for the requested real target.

    LAB_GREEN is terminal only for a LAB target. For PREPROD/PROD it remains in
    the queue as PROMOTION_REQUIRED so 177/177 LAB green can never collapse the
    real-environment audit queue to zero.
    """
    if target_environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid target environment")

    rows = []
    for row in matrix:
        state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
        if state not in PRIORITY:
            raise ValueError(f"unknown readiness state: {state}")
        engine_id = row["engine_id"]
        row_company = row.get("company_id")
        row_environment = row.get("environment")

        if company_id is not None and row_company not in {None, company_id, "GLOBAL"}:
            rows.append({
                "engine_id": engine_id,
                "state": state,
                "priority": 0,
                "reason": "COMPANY_SCOPE_MISMATCH",
                "target_environment": target_environment,
            })
            continue

        if state == "CONFIRMED_OPERATIONAL" and row_environment in {None, target_environment}:
            continue
        if state == "LAB_GREEN" and target_environment == "LAB" and row_environment in {None, "LAB"}:
            continue

        reason = "READINESS_GAP"
        if state == "LAB_GREEN" and target_environment in {"PREPROD", "PROD"}:
            reason = "PROMOTION_REQUIRED"
        elif row_environment not in {None, target_environment}:
            reason = "ENVIRONMENT_SCOPE_MISMATCH"

        rows.append({
            "engine_id": engine_id,
            "state": state,
            "priority": PRIORITY[state],
            "reason": reason,
            "target_environment": target_environment,
        })
    return tuple(sorted(rows, key=lambda item: (item["priority"], item["engine_id"])))
