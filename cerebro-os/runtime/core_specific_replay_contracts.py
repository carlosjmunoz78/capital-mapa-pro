from __future__ import annotations

LEGACY_CORE_REPLAY = {
    9524837: {
        "name": "FENIX · CORE · Idempotencia y Run ID · V1",
        "runtime": "idempotency.py",
        "old_statuses": ("FIRST_SEEN", "BLOCKED_DUPLICATE"),
        "old_environment": "TEST",
        "old_external_action": False,
        "runtime_invariants": {
            "first_seen_status": "FIRST_SEEN",
            "duplicate_status": "BLOCKED_DUPLICATE",
            "scope_fields": ("company_id", "engine_id", "environment", "version"),
        },
    },
    9527140: {
        "name": "FENIX · CORE · Router Maestro · V1",
        "runtime": "router.py",
        "old_statuses": ("ROUTED_TO_FACEBOOK_ANALYTICS_TEST", "OK"),
        "old_environment": "TEST",
        "old_external_action": False,
        "runtime_invariants": {
            "route_status": "ROUTED_TO_FACEBOOK_ANALYTICS_TEST",
            "destination": "FACEBOOK_ANALYTICS_TEST",
            "external_action_executed": False,
        },
    },
    9527162: {
        "name": "FENIX · CORE · Logs universales · V1",
        "runtime": "execution_log.py",
        "old_statuses": ("STARTED", "OK"),
        "old_environment": "TEST",
        "old_external_action": False,
        "runtime_invariants": {
            "phases": ("start", "final"),
            "start_status": "STARTED",
            "final_status": "OK",
            "same_run_id_required": True,
        },
    },
    9537817: {
        "name": "FENIX · CORE · Dispatcher universal Notion → Redes · V1",
        "runtime": "dispatcher.py",
        "old_statuses": ("CANDIDATES_CLASSIFIED_NO_EXECUTION", "ROUTE_PREPARED_ENGINE_OFF"),
        "old_environment": "GLOBAL",
        "old_external_action": False,
        "runtime_invariants": {
            "query_status": "CANDIDATES_CLASSIFIED_NO_EXECUTION",
            "eligible_status": "ROUTE_PREPARED_ENGINE_OFF",
            "platform_state": "NOT_CALLED",
            "external_action_allowed": False,
            "t48_required": True,
        },
    },
}


def get_contract(scenario_id: int) -> dict:
    try:
        return LEGACY_CORE_REPLAY[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown legacy core replay scenario") from exc


def replay_readiness(scenario_id: int, *, live_contract_captured: bool, runtime_present: bool, replay_fixture_present: bool, rollback_proven: bool) -> dict:
    contract = get_contract(scenario_id)
    checks = {
        "live_contract_captured": live_contract_captured,
        "runtime_present": runtime_present,
        "replay_fixture_present": replay_fixture_present,
        "rollback_proven": rollback_proven,
    }
    green = all(checks.values())
    return {
        "scenario_id": scenario_id,
        "runtime": contract["runtime"],
        "checks": checks,
        "status": "GREEN_CODE_CI" if green else "PARITY_PENDING",
        "old_preserved": True,
        "autoactivate_old_allowed": False,
        "delete_old_allowed": False,
        "external_action_allowed": False,
        "prod_cutover_allowed": False,
    }
