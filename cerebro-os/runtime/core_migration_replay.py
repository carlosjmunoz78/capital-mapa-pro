from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    input_payload: dict[str, Any]
    expected_output: dict[str, Any]


def compare_old_new(
    *,
    company_id: str,
    engine_id: str,
    environment: str,
    version: str,
    cases: tuple[ReplayCase, ...],
    new_runtime: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Pure replay gate for migrating legacy CORE logic without touching the legacy system.

    The expected output is an immutable capture of the OLD behavior. The NEW runtime is
    executed only against supplied replay payloads. No external mutation is permitted by
    this contract. Promotion is allowed only when every replay case is exactly equivalent.
    """
    if not all((company_id, engine_id, environment, version)):
        raise ValueError("company_id, engine_id, environment and version are required")
    if environment not in {"LAB", "PREPROD"}:
        raise ValueError("replay is restricted to LAB/PREPROD")
    if not cases:
        raise ValueError("at least one replay case is required")

    mismatches: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for case in cases:
        actual = new_runtime(dict(case.input_payload))
        if not isinstance(actual, dict):
            raise ValueError("new_runtime must return dict")
        equal = actual == case.expected_output
        results.append({"case_id": case.case_id, "equal": equal})
        if not equal:
            mismatches.append({
                "case_id": case.case_id,
                "expected": case.expected_output,
                "actual": actual,
            })

    green = not mismatches
    return {
        "company_id": company_id,
        "engine_id": engine_id,
        "environment": environment,
        "version": version,
        "cases_total": len(cases),
        "cases_green": sum(1 for item in results if item["equal"]),
        "mismatches": tuple(mismatches),
        "old_preserved": True,
        "external_mutation_allowed": False,
        "delete_old_allowed": False,
        "cutover_allowed": green,
        "status": "GREEN_CODE_CI" if green else "PARITY_RED",
    }
