from __future__ import annotations

from dataclasses import dataclass

SAAS_READ_APPS = {"facebook-pages", "instagram-business", "linkedin", "youtube", "google-search-console", "google-analytics-4"}
EXTERNAL_MUTATOR_APPS = {"wordpress", "openai-gpt-3", "google-drive"}
DETERMINISTIC_HINTS = (
    "router", "preflight", "idempotencia", "run id", "logs", "dispatcher",
    "validación", "normalización", "detector", "generador ventanas", "cierre técnico",
)


@dataclass(frozen=True)
class CoreInactiveScenario:
    scenario_id: int
    name: str
    apps: tuple[str, ...]
    incomplete_executions: int = 0


def classify_core_inactive(item: CoreInactiveScenario) -> dict:
    name = item.name.casefold()
    apps = set(item.apps)

    if item.incomplete_executions:
        return _result(item, "BLOCKED_REVIEW", "HIGH_RISK")

    if "tiktok" in name:
        return _result(item, "PARKED_ACCOUNT_NOT_AVAILABLE", None)

    if any(token in name for token in ("no usar", "fallida", "no canónica", "temporal", " temp")):
        if "migrar a nativo" in name:
            return _result(item, "MIGRATE_TO_NATIVE_RUNTIME_KEEP_INACTIVE", None)
        return _result(item, "QUARANTINE_HISTORICAL", None)

    if "pre-prod" in name and "wordpress" in name:
        return _result(item, "KEEP_QUARANTINED_FAIL_CLOSED", None)

    if "fábrica" in name:
        return _result(item, "MIGRATE_TO_ENGINE_FACTORY_RUNTIME", None)

    if any(hint in name for hint in DETERMINISTIC_HINTS):
        return _result(item, "MIGRATE_DETERMINISTIC_LOGIC_TO_RUNTIME", None)

    if apps & SAAS_READ_APPS:
        return _result(item, "KEEP_SAAS_READ_EDGE_WRAP", None)

    if apps & EXTERNAL_MUTATOR_APPS:
        return _result(item, "KEEP_INACTIVE_EXTERNAL_MUTATOR_QUARANTINE", None)

    if "test" in name or "auditoría" in name:
        return _result(item, "KEEP_INACTIVE_EVIDENCE", None)

    return _result(item, "MIGRATE_DETERMINISTIC_LOGIC_TO_RUNTIME", None)


def _result(item: CoreInactiveScenario, disposition: str, human_reason: str | None) -> dict:
    return {
        "scenario_id": item.scenario_id,
        "disposition": disposition,
        "delete_allowed": False,
        "auto_activate_allowed": False,
        "external_action_allowed": False,
        "old_preserved": True,
        "human_required": human_reason is not None,
        "human_reason": human_reason,
    }
