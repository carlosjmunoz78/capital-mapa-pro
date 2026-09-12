from __future__ import annotations

from dataclasses import dataclass

MUTATOR_APPS = {
    "facebook-pages",
    "instagram-business",
    "linkedin",
    "youtube",
    "wordpress",
    "notion",
    "http",
}


@dataclass(frozen=True)
class MakeScenarioMeta:
    scenario_id: int
    name: str
    status: str
    is_active: bool
    apps: tuple[str, ...]
    incomplete_executions: int = 0


def classify_scenario(meta: MakeScenarioMeta) -> dict:
    name = meta.name.strip()
    upper = name.upper()
    apps = set(meta.apps)
    mutating_surface = bool(apps & MUTATOR_APPS)

    if meta.incomplete_executions:
        return _result(meta, "REVIEW_REQUIRED", "HIGH_RISK", mutating_surface)

    if meta.is_active or meta.status == "active":
        return _result(meta, "PRESERVE_ACTIVE_EDGE", None, mutating_surface)

    if meta.status == "error":
        return _result(meta, "ARCHIVE_TRACEABILITY_DO_NOT_RUN", None, mutating_surface)

    if "DEPRECATED" in upper or "NO USAR" in upper:
        return _result(meta, "QUARANTINE_DEPRECATED", None, mutating_surface)

    if "FIXTURE" in upper:
        return _result(meta, "QUARANTINE_FIXTURE", None, mutating_surface)

    if "TEMP" in upper or "TEMPORAL" in upper:
        return _result(meta, "QUARANTINE_TEMPORARY", None, mutating_surface)

    if mutating_surface:
        return _result(meta, "KEEP_INACTIVE_WRAP_AND_TEST", None, True)

    return _result(meta, "KEEP_INACTIVE_READ_ONLY_OR_LOGIC", None, False)


def _result(meta: MakeScenarioMeta, classification: str, human_reason: str | None, mutating_surface: bool) -> dict:
    return {
        "scenario_id": meta.scenario_id,
        "classification": classification,
        "mutating_surface": mutating_surface,
        "delete_allowed": False,
        "auto_activate_allowed": False,
        "external_action_allowed": False,
        "human_required": human_reason is not None,
        "human_reason": human_reason,
    }
