from __future__ import annotations

ALLOWED_STATES_BY_ENVIRONMENT = {
    "LAB": {"LAB_GREEN", "CONFIRMED_OPERATIONAL"},
    "PREPROD": {"CONFIRMED_OPERATIONAL"},
    "PROD": {"CONFIRMED_OPERATIONAL"},
}


def system_readiness(*, canonical_ids, matrix, environment: str = "LAB", company_id: str | None = None) -> dict:
    """Evaluate one explicit system scope.

    The gate defaults to LAB only for backwards compatibility with the canonical
    177 LAB test. PREPROD/PROD can never inherit LAB_GREEN as system green.
    When company_id is provided, rows from another tenant are rejected from the
    evaluated scope instead of being silently counted.
    """
    canonical = tuple(canonical_ids)
    if len(canonical) != 177 or len(set(canonical)) != 177:
        raise ValueError("system gate requires exactly 177 unique canonical engines")
    if environment not in ALLOWED_STATES_BY_ENVIRONMENT:
        raise ValueError("invalid environment")

    by_id: dict[str, dict] = {}
    duplicate_rows: list[str] = []
    out_of_scope_rows: list[str] = []
    for row in matrix:
        engine_id = row.get("engine_id")
        if engine_id not in canonical:
            continue
        row_env = row.get("environment")
        row_company = row.get("company_id")
        if row_env not in {None, environment}:
            out_of_scope_rows.append(engine_id)
            continue
        if company_id is not None and row_company not in {None, company_id}:
            out_of_scope_rows.append(engine_id)
            continue
        if engine_id in by_id:
            duplicate_rows.append(engine_id)
            continue
        by_id[engine_id] = row

    missing_rows = tuple(engine_id for engine_id in canonical if engine_id not in by_id)
    allowed_states = ALLOWED_STATES_BY_ENVIRONMENT[environment]
    not_green = tuple(
        engine_id
        for engine_id in canonical
        if engine_id in by_id and by_id[engine_id].get("state") not in allowed_states
    )
    green_count = len(canonical) - len(missing_rows) - len(not_green)
    scope_errors = tuple(sorted(set(duplicate_rows + out_of_scope_rows)))
    return {
        "state": "GREEN" if not missing_rows and not not_green and not scope_errors else "RED",
        "total": len(canonical),
        "green_count": green_count,
        "missing_rows": missing_rows,
        "not_green": not_green,
        "scope_errors": scope_errors,
        "environment": environment,
        "company_id": company_id,
    }
