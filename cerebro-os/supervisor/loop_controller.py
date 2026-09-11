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


def _is_terminal_green(row: dict, *, target_environment: str, company_id: str | None) -> bool:
    state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
    row_environment = row.get("environment")
    row_company = row.get("company_id")
    evidence = tuple(row.get("evidence_refs", ()))
    if company_id is not None and row_company not in {None, company_id, "GLOBAL"}:
        return False
    if target_environment == "LAB":
        return state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"} and row_environment in {None, "LAB"} and bool(evidence)
    return state == "CONFIRMED_OPERATIONAL" and row_environment == target_environment and bool(evidence)


def select_next_engine(matrix, *, target_environment: str = "LAB", company_id: str | None = None) -> dict | None:
    if target_environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid target_environment")
    candidates = []
    for row in matrix:
        state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
        if _is_terminal_green(row, target_environment=target_environment, company_id=company_id):
            continue
        if state not in PRIORITY:
            raise ValueError(f"unsupported state: {state}")
        # LAB_GREEN must remain selectable for PREPROD/PROD promotion work.
        effective_priority = PRIORITY[state]
        candidates.append((effective_priority, row["engine_id"], row))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item[0], item[1]))[0][2]


def next_action(row: dict, *, target_environment: str = "LAB", company_id: str | None = None) -> dict:
    if target_environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid target_environment")
    state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
    engine_id = row.get("engine_id")
    if not engine_id:
        raise ValueError("engine_id required")
    if company_id is not None and row.get("company_id") not in {None, company_id, "GLOBAL"}:
        return {"engine_id": engine_id, "action": "SCOPE_AUDIT", "auto": True}
    if _is_terminal_green(row, target_environment=target_environment, company_id=company_id):
        return {"engine_id": engine_id, "action": "SKIP_GREEN", "auto": True}
    if state == "BLOCKED":
        return {"engine_id": engine_id, "action": "BLOCKED", "auto": False}
    if state == "HUMAN_REQUIRED":
        return {"engine_id": engine_id, "action": "HUMAN_REQUIRED", "auto": False}
    if state == "UNKNOWN_REQUIRES_AUDIT":
        return {"engine_id": engine_id, "action": "AUDIT", "auto": True}
    if state in {"DOCUMENTED_PARTIAL", "DEFINED_NOT_BUILT"}:
        return {"engine_id": engine_id, "action": "GAP_ANALYSIS", "auto": True}
    if state == "LAB_GREEN" and target_environment in {"PREPROD", "PROD"}:
        return {"engine_id": engine_id, "action": "PROMOTION_GAP_ANALYSIS", "auto": True}
    if state == "CONFIRMED_OPERATIONAL":
        return {"engine_id": engine_id, "action": "SCOPE_AUDIT", "auto": True}
    raise ValueError(f"unsupported state: {state}")


def gap_plan(*, engine_id: str, missing: tuple[str, ...] | list[str], auto_safe: set[str]) -> dict:
    safe = tuple(item for item in missing if item in auto_safe)
    review = tuple(item for item in missing if item not in auto_safe)
    return {
        "engine_id": engine_id,
        "safe_autofix": safe,
        "review_required": review,
        "next": "SAFE_AUTOFIX" if safe else ("REVIEW_REQUIRED" if review else "TEST_REQUIRED"),
    }
