"""Operator capability policy for incremental Browser Bridge and desktop control.

Planner only. The installed v1.5 extension supports exactly fixed-host metadata;
a GREEN policy verdict is NEVER permission to dispatch an unimplemented command.
Existing computer_use_policy.py still applies in addition to this boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

SUPPORTED_ACTIONS = frozenset({
    "NAVIGATE", "READ_PAGE", "CLICK", "TYPE", "SUBMIT_FORM",
    "UPLOAD_FILE", "DOWNLOAD_FILE", "DESKTOP_READ", "DESKTOP_CLICK",
})
WRITE_ACTIONS = frozenset({"TYPE", "SUBMIT_FORM", "UPLOAD_FILE", "DESKTOP_CLICK"})
HIGH_RISK_ACTIONS = frozenset({
    "PUBLISH", "SEND_MESSAGE", "SEND_EMAIL", "DELETE", "PAYMENT",
    "LEGAL_ACCEPTANCE", "BINDING_SIGNATURE", "ROTATE_CREDENTIAL",
    "INSTALL_SOFTWARE",
})
CANONICAL_HUMAN_REASONS = frozenset({
    "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
    "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST",
})


@dataclass(frozen=True)
class OperatorRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    device_id: str
    profile_id: str
    origin: str
    action: str
    target_ref: str
    idempotency_key: str
    audit_ref: str
    approved_origins: tuple[str, ...]
    connector_available: bool
    browser_fresh: bool
    policy_green: bool
    kill_switch_enabled: bool
    audit_available: bool
    data_contract_green: bool
    snapshot_available: bool
    rollback_tested: bool
    preprod_old_new_green: bool
    action_approved: bool = False
    confidence: float = 1.0
    money_amount: float = 0.0
    money_limit: float = 0.0
    legal_required: bool = False
    signature_required: bool = False
    customer_human_request: bool = False
    security_incident: bool = False


def _canonical_origin(origin: str) -> bool:
    try:
        p = urlsplit(origin)
        host = p.hostname or ""
        return bool(
            p.scheme == "https" and host and "." in host
            and not p.username and not p.password and p.port is None
            and p.path in ("", "/") and not p.query and not p.fragment
            and origin == f"https://{host}/"
            and all(
                label and label[0].isalnum() and label[-1].isalnum()
                and all(c.isalnum() or c == "-" for c in label)
                for label in host.split(".")
            )
        )
    except ValueError:
        return False


def plan_operator_action(req: OperatorRequest, *, implemented_actions: frozenset[str]) -> dict:
    """Pure deterministic policy. No browser calls, credentials or side effects."""
    required = (
        req.company_id, req.engine_id, req.environment, req.version,
        req.device_id, req.profile_id, req.origin, req.action,
        req.target_ref, req.idempotency_key, req.audit_ref,
    )
    if not all(x and str(x).strip() for x in required):
        raise ValueError("OPERATOR_SCOPE_REQUIRED")
    if not 0 <= req.confidence <= 1 or req.money_amount < 0 or req.money_limit < 0:
        raise ValueError("OPERATOR_NUMERIC_SCOPE_INVALID")

    blockers: list[str] = []
    human: list[str] = []
    if req.company_id != "fenix" or req.environment != "LAB" or req.version != "v0":
        blockers.append("LAB_FIRST_SCOPE_REQUIRED")
    if not _canonical_origin(req.origin) or req.origin not in req.approved_origins:
        blockers.append("ORIGIN_APPROVAL_REQUIRED")
    if req.connector_available:
        blockers.append("CONNECTOR_FIRST")
    if not req.browser_fresh:
        blockers.append("BROWSER_HEARTBEAT_REQUIRED")
    if not req.kill_switch_enabled or not req.audit_available:
        blockers.append("SAFETY_RUNTIME_REQUIRED")
    if not req.policy_green:
        blockers.append("POLICY_NOT_GREEN")
        human.append("POLICY_CONFLICT")
    if req.confidence < 0.85:
        blockers.append("CONFIDENCE_BELOW_THRESHOLD")
        human.append("LOW_CONFIDENCE")
    if req.action not in SUPPORTED_ACTIONS and req.action not in HIGH_RISK_ACTIONS:
        blockers.append("ACTION_UNKNOWN")
    if req.action in HIGH_RISK_ACTIONS:
        blockers.append("HIGH_RISK_ACTION_NOT_AUTONOMOUS")
        human.append("HIGH_RISK")
    if req.action in WRITE_ACTIONS and not req.action_approved:
        blockers.append("WRITE_ACTION_APPROVAL_REQUIRED")
        human.append("HIGH_RISK")
    if req.action in WRITE_ACTIONS and not all((
        req.data_contract_green, req.snapshot_available,
        req.rollback_tested, req.preprod_old_new_green,
    )):
        blockers.append("MUTATION_RELEASE_GATES_REQUIRED")
    if req.money_amount > req.money_limit:
        blockers.append("MONEY_LIMIT")
        human.append("MONEY_LIMIT")
    if req.legal_required:
        blockers.append("LEGAL_REQUIRED")
        human.append("LEGAL_REQUIRED")
    if req.signature_required:
        blockers.append("SIGNATURE_REQUIRED")
        human.append("SIGNATURE_REQUIRED")
    if req.customer_human_request:
        blockers.append("CUSTOMER_HUMAN_REQUEST")
        human.append("CUSTOMER_HUMAN_REQUEST")
    if req.security_incident:
        blockers.append("SECURITY_INCIDENT")
        human.append("SECURITY_INCIDENT")
    if req.action not in implemented_actions:
        blockers.append("EXECUTOR_NOT_IMPLEMENTED")
    # The 1.5 fixed-host metadata pilot is separately implemented and scoped;
    # no broad action is considered implemented by this v0 contract.
    permitted = not blockers
    return {
        "record_type": "browser_full_operator_contract_v0",
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "action": req.action,
        "status": "GREEN" if permitted else "HUMAN_REQUIRED" if human else "BLOCKED",
        "dispatch_allowed": permitted,
        "blockers": tuple(dict.fromkeys(blockers)),
        "human_reasons": tuple(dict.fromkeys(human)),
        "credential_value_exposure_allowed": False,
        "secret_copy_to_prompt_allowed": False,
        "audit_required": True,
        "idempotency_required": True,
        "prod_activation_allowed": False,
        "cost_eur": 0.0,
    }
