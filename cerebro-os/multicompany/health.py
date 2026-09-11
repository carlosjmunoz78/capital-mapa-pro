from __future__ import annotations

VALID_ENGINE_STATES = {"GREEN", "RED", "HUMAN_REQUIRED", "BLOCKED", "UNKNOWN"}


def company_health(*, company_id: str, required_engines: tuple[str, ...], engine_states: dict[str, str], evidence_refs: dict[str, tuple[str, ...] | list[str]] | None = None) -> dict:
    if not company_id:
        raise ValueError("company_id required")
    unknown_values = {state for state in engine_states.values() if state not in VALID_ENGINE_STATES}
    if unknown_values:
        raise ValueError(f"invalid engine states: {sorted(unknown_values)}")
    evidence_refs = evidence_refs or {}
    missing = tuple(sorted(engine_id for engine_id in required_engines if engine_id not in engine_states))
    human = tuple(sorted(engine_id for engine_id in required_engines if engine_states.get(engine_id) == "HUMAN_REQUIRED"))
    bad = tuple(sorted(engine_id for engine_id in required_engines if engine_states.get(engine_id) in {"RED", "BLOCKED", "UNKNOWN"}))
    green_without_evidence = tuple(sorted(
        engine_id for engine_id in required_engines
        if engine_states.get(engine_id) == "GREEN" and not tuple(evidence_refs.get(engine_id, ()))
    ))
    if human:
        state = "HUMAN_REQUIRED"
    elif missing or bad or green_without_evidence:
        state = "RED"
    else:
        state = "GREEN"
    return {
        "company_id": company_id,
        "state": state,
        "missing": missing,
        "human_required": human,
        "not_green": bad,
        "green_without_evidence": green_without_evidence,
    }
