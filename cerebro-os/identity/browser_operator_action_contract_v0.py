"""Browser Operator action contract.

Defines how CEREBRO may progress from verified read-only navigation toward
browser operation. This module is policy only: it NEVER executes a browser
action and does not grant PROD permissions.
"""
from __future__ import annotations
from dataclasses import dataclass

READ_ONLY = frozenset({"NAVIGATE", "READ_METADATA", "READ_PAGE"})
REVERSIBLE_WRITE = frozenset({"CLICK", "TYPE", "SELECT", "UPLOAD", "DOWNLOAD", "SAVE_DRAFT"})
COMMIT_WRITE = frozenset({"SUBMIT_FORM", "PUBLISH", "SEND_MESSAGE", "CREATE_RECORD", "UPDATE_RECORD"})
HUMAN_ONLY = frozenset({"SIGN_LEGAL", "CONFIRM_PAYMENT", "ENTER_SECRET", "SOLVE_CAPTCHA"})
ALL = READ_ONLY | REVERSIBLE_WRITE | COMMIT_WRITE | HUMAN_ONLY


@dataclass(frozen=True)
class BrowserActionRequest:
    company_id: str
    environment: str
    version: str
    action: str
    origin_allowlisted: bool
    connector_available: bool
    policy_green: bool
    session_authorized: bool
    rollback_available: bool
    confidence: float
    involves_money: bool = False
    involves_legal_signature: bool = False
    customer_requested_human: bool = False
    security_incident: bool = False


def decide_browser_action(req: BrowserActionRequest) -> dict:
    blockers: list[str] = []
    human_reason = None
    if req.action not in ALL:
        blockers.append("UNKNOWN_ACTION")
    if req.company_id != "fenix" or req.environment != "LAB" or req.version != "v0":
        blockers.append("LAB_SCOPE_REQUIRED")
    if req.connector_available:
        blockers.append("CONNECTOR_FIRST")
    if not req.origin_allowlisted:
        blockers.append("ORIGIN_NOT_ALLOWLISTED")
    if not req.policy_green or not req.session_authorized:
        blockers.append("POLICY_OR_SESSION_NOT_AUTHORIZED")
    if req.action in REVERSIBLE_WRITE | COMMIT_WRITE and not req.rollback_available:
        blockers.append("ROLLBACK_REQUIRED")
    if not 0.0 <= req.confidence <= 1.0 or req.confidence < 0.90:
        human_reason = "LOW_CONFIDENCE"
    if req.involves_money or req.action == "CONFIRM_PAYMENT":
        human_reason = "MONEY_LIMIT"
    if req.involves_legal_signature or req.action == "SIGN_LEGAL":
        human_reason = "SIGNATURE_REQUIRED"
    if req.customer_requested_human:
        human_reason = "CUSTOMER_HUMAN_REQUEST"
    if req.security_incident:
        human_reason = "SECURITY_INCIDENT"
    if req.action in HUMAN_ONLY and human_reason is None:
        human_reason = "HIGH_RISK"

    # Current physical runtime v1.5 proves only fixed metadata navigation.
    # Never imply that this policy contract makes writes executable.
    runtime_implemented = req.action in {"NAVIGATE", "READ_METADATA"}
    if not runtime_implemented:
        blockers.append("RUNTIME_ACTION_NOT_IMPLEMENTED")

    decision = "HUMAN_REQUIRED" if human_reason else (
        "ALLOW" if not blockers else "BLOCK"
    )
    return {
        "record_type": "browser_operator_action_decision",
        "company_id": req.company_id,
        "engine_id": "ACCESSBOOT-001",
        "environment": req.environment,
        "version": req.version,
        "action": req.action,
        "decision": decision,
        "blockers": tuple(blockers),
        "human_reason": human_reason,
        "runtime_implemented": runtime_implemented,
        "external_mutation_allowed": bool(decision == "ALLOW" and req.action in REVERSIBLE_WRITE | COMMIT_WRITE),
        "prod_activation_allowed": False,
        "cost_eur": 0.0,
    }
