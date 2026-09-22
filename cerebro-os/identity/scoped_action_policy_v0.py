"""Deterministic action gates for CEREBRO Operator.

This is a planning contract, not a grant of browser/desktop permissions.
Connector-first; bounded low-risk authorized changes may be autonomous.
"""
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit


class ActionClass(str, Enum):
    READ = "READ"
    DRAFT = "DRAFT"
    INTERNAL_UPDATE = "INTERNAL_UPDATE"
    EXTERNAL_PUBLISH = "EXTERNAL_PUBLISH"
    CUSTOMER_SEND = "CUSTOMER_SEND"
    PURCHASE = "PURCHASE"
    CREDENTIAL = "CREDENTIAL"
    SECURITY_CHANGE = "SECURITY_CHANGE"
    LEGAL = "LEGAL"
    SIGNATURE = "SIGNATURE"


@dataclass(frozen=True)
class ScopedAction:
    company_id: str
    engine_id: str
    environment: str
    version: str
    action_id: str
    action_class: ActionClass
    target_origin: str
    approved_origins: tuple[str, ...]
    connector_available: bool
    identity_scoped: bool
    policy_green: bool
    backup_verified: bool
    rollback_verified: bool
    preprod_green: bool
    budget_eur: float
    budget_limit_eur: float
    customer_requests_human: bool = False
    security_incident: bool = False
    low_confidence: bool = False
    explicit_legal_requirement: bool = False
    signature_required: bool = False
    external_publication_approved: bool = False
    customer_send_approved: bool = False


def evaluate_action(request: ScopedAction) -> dict:
    blockers = []
    human = []
    if not all((request.company_id, request.engine_id, request.environment,
                request.version, request.action_id)):
        blockers.append("MULTICOMPANY_SCOPE_REQUIRED")
    if request.environment not in ("LAB", "PREPROD", "PROD"):
        blockers.append("ENVIRONMENT_DENIED")
    if not request.identity_scoped:
        blockers.append("IDENTITY_SCOPE_MISSING")
    if request.connector_available:
        blockers.append("CONNECTOR_FIRST")
    try:
        parsed = urlsplit(request.target_origin)
        canonical = "https://" + str(parsed.hostname or "") + "/"
        allowed = (parsed.scheme == "https" and parsed.hostname
                   and parsed.path in ("", "/") and not parsed.query
                   and not parsed.fragment and not parsed.username and not parsed.password
                   and parsed.port is None and request.target_origin == canonical
                   and request.target_origin in request.approved_origins)
        if not allowed:
            blockers.append("TARGET_ORIGIN_NOT_APPROVED")
    except ValueError:
        blockers.append("TARGET_ORIGIN_NOT_APPROVED")
    if not request.policy_green:
        human.append("POLICY_CONFLICT")
    if request.security_incident:
        human.append("SECURITY_INCIDENT")
    if request.low_confidence:
        human.append("LOW_CONFIDENCE")
    if request.customer_requests_human:
        human.append("CUSTOMER_HUMAN_REQUEST")
    if request.explicit_legal_requirement or request.action_class is ActionClass.LEGAL:
        human.append("LEGAL_REQUIRED")
    if request.signature_required or request.action_class is ActionClass.SIGNATURE:
        human.append("SIGNATURE_REQUIRED")
    if not (0 <= request.budget_eur <= request.budget_limit_eur):
        human.append("MONEY_LIMIT")
    if request.action_class in (ActionClass.PURCHASE, ActionClass.CREDENTIAL,
                                ActionClass.SECURITY_CHANGE):
        human.append("HIGH_RISK")
    if request.action_class is ActionClass.EXTERNAL_PUBLISH and not request.external_publication_approved:
        blockers.append("PUBLISH_POLICY_APPROVAL_MISSING")
    if request.action_class is ActionClass.CUSTOMER_SEND and not request.customer_send_approved:
        blockers.append("CUSTOMER_SEND_POLICY_APPROVAL_MISSING")
    mutable = request.action_class is not ActionClass.READ
    if mutable and not all((request.backup_verified, request.rollback_verified,
                            request.preprod_green)):
        blockers.append("MUTATION_RELEASE_GATES_MISSING")
    if request.environment == "PROD" and not request.preprod_green:
        blockers.append("PROD_PREPROD_REQUIRED")
    if request.environment == "PROD" and not request.policy_green:
        blockers.append("PROD_POLICY_REQUIRED")
    # Browser write executor is still restricted to the local LAB fixture;
    # approval here does not imply execution of an arbitrary browser action.
    if mutable and request.target_origin != "https://example.com/":
        blockers.append("BROWSER_WRITE_RUNTIME_NOT_IMPLEMENTED")
    if mutable and request.target_origin == "https://example.com/":
        blockers.append("EXTERNAL_WRITE_RUNTIME_NOT_IMPLEMENTED")
    if human:
        decision = "HUMAN_REQUIRED"
    elif blockers:
        decision = "BLOCKED"
    else:
        decision = "POLICY_GREEN_NOT_EXECUTED"
    return {
        "company_id": request.company_id,
        "engine_id": request.engine_id,
        "environment": request.environment,
        "version": request.version,
        "action_id": request.action_id,
        "decision": decision,
        "human_reasons": tuple(dict.fromkeys(human)),
        "blockers": tuple(dict.fromkeys(blockers)),
        "external_write_permitted": False,
        "runtime_dispatch_permitted": False,
        "cost_eur": 0.0,
    }
