from __future__ import annotations

VALID_ENGINE_STATES = {"GREEN", "RED", "HUMAN_REQUIRED", "BLOCKED", "UNKNOWN"}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def company_health(*, company_id: str, required_engines: tuple[str, ...], engine_states: dict[str, str], evidence_refs: dict[str, tuple[str, ...] | list[str]] | None = None, environment: str = "LAB", version: str = "1.0.0", evidence_scopes: dict[str, dict[str, str]] | None = None) -> dict:
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id and version required")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")
    unknown_values = {state for state in engine_states.values() if state not in VALID_ENGINE_STATES}
    if unknown_values:
        raise ValueError(f"invalid engine states: {sorted(unknown_values)}")
    evidence_refs = evidence_refs or {}
    evidence_scopes = evidence_scopes or {}
    missing = tuple(sorted(engine_id for engine_id in required_engines if engine_id not in engine_states))
    human = tuple(sorted(engine_id for engine_id in required_engines if engine_states.get(engine_id) == "HUMAN_REQUIRED"))
    bad = tuple(sorted(engine_id for engine_id in required_engines if engine_states.get(engine_id) in {"RED", "BLOCKED", "UNKNOWN"}))
    green_without_evidence = tuple(sorted(
        engine_id for engine_id in required_engines
        if engine_states.get(engine_id) == "GREEN" and not tuple(ref for ref in evidence_refs.get(engine_id, ()) if isinstance(ref, str) and ref.strip())
    ))
    scope_mismatch = tuple(sorted(
        engine_id for engine_id in required_engines
        if engine_states.get(engine_id) == "GREEN"
        and (
            evidence_scopes.get(engine_id, {}).get("company_id") != company_id
            or evidence_scopes.get(engine_id, {}).get("environment") != environment
            or evidence_scopes.get(engine_id, {}).get("version") != version
        )
    ))
    if human:
        state = "HUMAN_REQUIRED"
    elif missing or bad or green_without_evidence or scope_mismatch:
        state = "RED"
    else:
        state = "GREEN"
    return {
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "state": state,
        "missing": missing,
        "human_required": human,
        "not_green": bad,
        "green_without_evidence": green_without_evidence,
        "scope_mismatch": scope_mismatch,
    }
