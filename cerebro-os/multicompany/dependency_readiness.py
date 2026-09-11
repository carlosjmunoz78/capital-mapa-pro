from __future__ import annotations

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def dependency_readiness(
    *,
    active_engines: set[str],
    dependencies: dict[str, tuple[str, ...] | list[str]],
    evidence_by_engine: dict[str, dict[str, str]] | None = None,
    company_id: str = "GLOBAL",
    environment: str = "LAB",
    version: str = "1.0.0",
) -> dict:
    """Evaluate dependency closure only when active-engine claims are evidenced.

    An engine being present in ``active_engines`` is not sufficient proof that it
    is active for the requested tenant/release. Every active engine must carry a
    non-empty evidence reference plus exact company/environment/version scope.
    """
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id and version required")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")
    evidence_by_engine = evidence_by_engine or {}

    missing: dict[str, tuple[str, ...]] = {}
    evidence_missing: list[str] = []
    scope_mismatch: list[str] = []
    for engine_id in sorted(active_engines):
        proof = evidence_by_engine.get(engine_id, {})
        if not str(proof.get("evidence_ref", "")).strip():
            evidence_missing.append(engine_id)
        if (
            proof.get("company_id") != company_id
            or proof.get("environment") != environment
            or proof.get("version") != version
        ):
            scope_mismatch.append(engine_id)
        deps = tuple(dependencies.get(engine_id, ()))
        absent = tuple(sorted(dep for dep in deps if dep not in active_engines))
        if absent:
            missing[engine_id] = absent
    return {
        "ready": not missing and not evidence_missing and not scope_mismatch,
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "missing_dependencies": missing,
        "evidence_missing": tuple(evidence_missing),
        "scope_mismatch": tuple(scope_mismatch),
    }


def validate_dependency_ids(*, canonical_ids: set[str], dependencies: dict[str, tuple[str, ...] | list[str]]) -> None:
    unknown: set[str] = set()
    for engine_id, deps in dependencies.items():
        if engine_id not in canonical_ids:
            unknown.add(engine_id)
        unknown.update(dep for dep in deps if dep not in canonical_ids)
    if unknown:
        raise ValueError(f"unknown canonical ids in dependency map: {sorted(unknown)}")
