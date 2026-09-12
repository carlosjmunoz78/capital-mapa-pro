from __future__ import annotations

from dataclasses import dataclass

HUMAN_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

FORBIDDEN_AUTONOMOUS_ACTIONS = {
    "LEGAL_ACCEPTANCE",
    "BINDING_SIGNATURE",
    "PAYMENT_ABOVE_LIMIT",
    "SECURITY_RECOVERY",
    "DELETE_CRITICAL_ACCOUNT",
    "ROTATE_ROOT_CREDENTIAL",
}


@dataclass(frozen=True)
class ComputerUseRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    capability: str
    action: str
    higher_priority_connector_available: bool
    account_registered: bool
    credential_reference_available: bool
    policy_green: bool
    confidence: float
    money_amount: float = 0.0
    money_limit: float = 0.0
    explicit_customer_human_request: bool = False

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.environment,
            self.version,
            self.capability,
            self.action,
        )
        if any(not str(v).strip() for v in required):
            raise ValueError("computer-use request missing scope/input")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.money_amount < 0 or self.money_limit < 0:
            raise ValueError("money values must be non-negative")


def evaluate_computer_use(req: ComputerUseRequest) -> dict:
    req.validate()

    human_reason = None
    blockers = []

    if req.higher_priority_connector_available:
        blockers.append("USE_HIGHER_PRIORITY_CONNECTOR")
    if not req.account_registered:
        blockers.append("ACCOUNT_NOT_REGISTERED")
    if not req.credential_reference_available:
        blockers.append("CREDENTIAL_REFERENCE_MISSING")
    if not req.policy_green:
        blockers.append("POLICY_NOT_GREEN")
        human_reason = "POLICY_CONFLICT"
    if req.confidence < 0.85:
        blockers.append("LOW_CONFIDENCE")
        human_reason = human_reason or "LOW_CONFIDENCE"
    if req.action in FORBIDDEN_AUTONOMOUS_ACTIONS:
        blockers.append("HUMAN_ONLY_ACTION")
        if req.action == "LEGAL_ACCEPTANCE":
            human_reason = human_reason or "LEGAL_REQUIRED"
        elif req.action == "BINDING_SIGNATURE":
            human_reason = human_reason or "SIGNATURE_REQUIRED"
        elif req.action == "PAYMENT_ABOVE_LIMIT":
            human_reason = human_reason or "MONEY_LIMIT"
        else:
            human_reason = human_reason or "HIGH_RISK"
    if req.money_amount > req.money_limit:
        blockers.append("MONEY_LIMIT")
        human_reason = human_reason or "MONEY_LIMIT"
    if req.explicit_customer_human_request:
        blockers.append("CUSTOMER_HUMAN_REQUEST")
        human_reason = human_reason or "CUSTOMER_HUMAN_REQUEST"

    allowed = not blockers
    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "capability": req.capability,
        "action": req.action,
        "computer_use_allowed": allowed,
        "browser_fallback_allowed": allowed,
        "kill_switch_required": True,
        "audit_log_required": True,
        "credential_value_exposure_allowed": False,
        "secret_copy_to_prompt_allowed": False,
        "blockers": tuple(blockers),
        "human_required": human_reason is not None,
        "human_reason": human_reason,
    }
