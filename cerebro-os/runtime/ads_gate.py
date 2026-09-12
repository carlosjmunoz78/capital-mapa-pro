from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class AdsOrder:
    company_id: str
    engine_id: str
    environment: str
    version: str
    ads_order_id: str
    run_id: str
    network: str
    route_type: str
    ad_account_id: str
    objective: str
    budget_amount: float
    currency: str
    budget_authorized: bool
    creative_ready: bool
    qa_passed: bool
    human_authorized: bool

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.ads_order_id, self.run_id, self.network, self.route_type, self.ad_account_id, self.objective, self.currency)
        if any(not str(v).strip() for v in required):
            raise ValueError("ads order missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.budget_amount < 0:
            raise ValueError("budget_amount must be non-negative")

    @property
    def idempotency_key(self) -> str:
        return f"ADS_PREFLIGHT:{self.company_id}:{self.environment}:{self.version}:{self.network}:{self.ads_order_id}"


def evaluate_ads_preflight(order: AdsOrder, *, duplicate_exists: bool = False) -> dict:
    order.validate()
    contract_ok = (
        order.route_type.upper() == "ADS"
        and order.budget_authorized
        and order.creative_ready
        and order.qa_passed
        and order.human_authorized
        and not duplicate_exists
    )
    status = "ADS_PREFLIGHT_READY_ENGINE_DISABLED" if contract_ok else "BLOCKED_PREFLIGHT"
    return {
        "company_id": order.company_id,
        "engine_id": order.engine_id,
        "environment": order.environment,
        "version": order.version,
        "ads_order_id": order.ads_order_id,
        "run_id": order.run_id,
        "idempotency_key": order.idempotency_key,
        "status": status,
        "route_receipt_status": "ADS_ROUTED_NO_EXTERNAL_ACTION" if contract_ok else "NOT_ROUTED",
        "requires_human": True,
        "external_action_allowed": False,
    }
