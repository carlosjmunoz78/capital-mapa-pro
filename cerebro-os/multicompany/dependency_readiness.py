from __future__ import annotations


def dependency_readiness(*, active_engines: set[str], dependencies: dict[str, tuple[str, ...] | list[str]]) -> dict:
    missing: dict[str, tuple[str, ...]] = {}
    for engine_id in sorted(active_engines):
        deps = tuple(dependencies.get(engine_id, ()))
        absent = tuple(sorted(dep for dep in deps if dep not in active_engines))
        if absent:
            missing[engine_id] = absent
    return {
        "ready": not missing,
        "missing_dependencies": missing,
    }


def validate_dependency_ids(*, canonical_ids: set[str], dependencies: dict[str, tuple[str, ...] | list[str]]) -> None:
    unknown: set[str] = set()
    for engine_id, deps in dependencies.items():
        if engine_id not in canonical_ids:
            unknown.add(engine_id)
        unknown.update(dep for dep in deps if dep not in canonical_ids)
    if unknown:
        raise ValueError(f"unknown canonical ids in dependency map: {sorted(unknown)}")
