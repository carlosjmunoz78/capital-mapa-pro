from __future__ import annotations


def loop_transition(
    *,
    state: str,
    audit_complete: bool = False,
    missing=(),
    safe_autofix_remaining=(),
    review_required=(),
    tests_green: bool = False,
    evidence_present: bool = False,
) -> dict:
    # A claimed green state is only terminal when the minimum proof is present.
    # This prevents stale/prose-only state from short-circuiting the loop.
    if state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"}:
        if not tests_green:
            return {"phase": "TEST", "result": "IN_PROGRESS"}
        if not evidence_present:
            return {"phase": "EVIDENCE", "result": "IN_PROGRESS"}
        return {"phase": "DONE", "result": "GREEN"}
    if state == "HUMAN_REQUIRED":
        return {"phase": "STOP", "result": "HUMAN_REQUIRED"}
    if state == "BLOCKED":
        return {"phase": "STOP", "result": "BLOCKED"}
    if not audit_complete:
        return {"phase": "AUDIT", "result": "IN_PROGRESS"}
    if safe_autofix_remaining:
        return {"phase": "SAFE_AUTOFIX", "result": "IN_PROGRESS", "items": tuple(safe_autofix_remaining)}
    if review_required:
        return {"phase": "REVIEW", "result": "BLOCKED", "items": tuple(review_required)}
    if missing:
        return {"phase": "GAP", "result": "IN_PROGRESS", "items": tuple(missing)}
    if not tests_green:
        return {"phase": "TEST", "result": "IN_PROGRESS"}
    if not evidence_present:
        return {"phase": "EVIDENCE", "result": "IN_PROGRESS"}
    return {"phase": "GREEN", "result": "LAB_GREEN"}


def system_loop_status(*, canonical_count: int, green_count: int, blocked_count: int = 0, human_count: int = 0) -> dict:
    if canonical_count != 177:
        raise ValueError("canonical_count must be 177")
    if min(green_count, blocked_count, human_count) < 0:
        raise ValueError("counts cannot be negative")
    if green_count > canonical_count:
        raise ValueError("green_count cannot exceed canonical_count")
    if blocked_count + human_count > canonical_count - green_count:
        raise ValueError("blocked/human counts cannot exceed non-green engines")

    pending = canonical_count - green_count
    if human_count:
        state = "HUMAN_REQUIRED"
    elif blocked_count:
        state = "RED"
    elif pending == 0:
        state = "GREEN"
    else:
        state = "RED"
    return {
        "state": state,
        "total": canonical_count,
        "green": green_count,
        "pending": pending,
        "blocked": blocked_count,
        "human_required": human_count,
    }
