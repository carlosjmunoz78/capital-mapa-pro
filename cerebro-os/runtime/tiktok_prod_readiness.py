from dataclasses import dataclass


TIKTOK_CORE_PREFLIGHT_SCENARIO = 9535460


@dataclass(frozen=True)
class TikTokProdReadinessEvidence:
    core_preflight_present: bool
    core_preflight_parity_green: bool
    official_oauth_connected: bool
    prod_executor_present: bool
    prod_executor_tested: bool
    rollback_proven: bool
    old_preserved: bool = True


def assess_tiktok_prod_readiness(e: TikTokProdReadinessEvidence) -> dict:
    gates = {
        "CORE_PREFLIGHT_MISSING": e.core_preflight_present,
        "CORE_PREFLIGHT_PARITY_NOT_GREEN": e.core_preflight_parity_green,
        "OFFICIAL_OAUTH_NOT_CONNECTED": e.official_oauth_connected,
        "PROD_EXECUTOR_MISSING": e.prod_executor_present,
        "PROD_EXECUTOR_NOT_TESTED": e.prod_executor_tested,
        "ROLLBACK_NOT_PROVEN": e.rollback_proven,
        "OLD_NOT_PRESERVED": e.old_preserved,
    }
    blockers = tuple(name for name, ok in gates.items() if not ok)
    permission_blocked = "OFFICIAL_OAUTH_NOT_CONNECTED" in blockers
    return {
        "core_preflight_scenario_id": TIKTOK_CORE_PREFLIGHT_SCENARIO,
        "status": "READY_FOR_EXPLICIT_EXECUTION" if not blockers else "BLOCKED",
        "blockers": blockers,
        "external_action_allowed": False,
        "delete_old_allowed": False,
        "requires_human": permission_blocked,
        "human_reason": "PERMISSION_REQUIRED" if permission_blocked else ("SIGNATURE_REQUIRED" if not blockers else None),
    }


def inventory() -> dict:
    return {
        "core_preflight": TIKTOK_CORE_PREFLIGHT_SCENARIO,
        "prod_executors": (),
    }
