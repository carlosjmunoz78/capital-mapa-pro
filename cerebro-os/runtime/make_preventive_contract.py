from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreventiveGateState:
    company_id: str
    engine_id: str
    environment: str
    version: str
    global_status: str
    facebook_status: str


def assess_facebook_test_gate(state: PreventiveGateState) -> dict:
    required = (state.company_id, state.engine_id, state.environment, state.version)
    if any(not str(v).strip() for v in required):
        raise ValueError("missing preventive gate scope")
    allowed = state.global_status == "BLOCKED_BY_DEFAULT" and state.facebook_status == "TEST_ONLY"
    return {
        "company_id": state.company_id,
        "engine_id": state.engine_id,
        "environment": state.environment,
        "version": state.version,
        "status": "ALLOWED_TEST" if allowed else "BLOCKED",
        "read_only_allowed": allowed,
        "publication_allowed": False,
        "notion_mutation_allowed": False,
        "external_mutation_allowed": False,
        "requires_human": False,
    }


@dataclass(frozen=True)
class DlqRecoveryObservation:
    company_id: str
    engine_id: str
    environment: str
    version: str
    operation_type: str
    platform_state: str
    attempts: int
    max_attempts: int
    idempotency_clear: bool


def assess_safe_retry(obs: DlqRecoveryObservation) -> dict:
    required = (obs.company_id, obs.engine_id, obs.environment, obs.version, obs.operation_type, obs.platform_state)
    if any(not str(v).strip() for v in required):
        raise ValueError("missing DLQ recovery scope")
    if obs.attempts < 0 or obs.max_attempts < 0:
        raise ValueError("attempt counts must be non-negative")

    temporary = obs.platform_state in {"TEMPORARY_TIMEOUT", "TEMPORARY_UNAVAILABLE", "RATE_LIMIT"}
    retry_safe = (
        obs.environment == "TEST"
        and obs.operation_type in {"analytics_capture", "read", "health_check"}
        and temporary
        and obs.attempts < obs.max_attempts
        and obs.idempotency_clear
    )
    return {
        "status": "SAFE_RETRY_APPROVED" if retry_safe else "RETRY_BLOCKED",
        "retry_read_allowed": retry_safe,
        "retry_publish_allowed": False,
        "external_mutation_allowed": False,
        "notion_mutation_allowed": False,
        "requires_human": False,
    }
