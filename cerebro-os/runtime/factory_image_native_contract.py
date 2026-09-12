from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
CANONICAL_HUMAN_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}


@dataclass(frozen=True)
class ImageAssetRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    run_id: str
    production_order_id: str
    format: str
    prompt: str
    existing_asset_count: int
    paid_provider_enabled: bool = False
    provider_cost_eur: float = 0.0
    money_limit_eur: float = 0.0

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.environment,
            self.version,
            self.run_id,
            self.production_order_id,
            self.format,
            self.prompt,
        )
        if any(not str(v).strip() for v in required):
            raise ValueError("image asset request missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.existing_asset_count < 0:
            raise ValueError("existing_asset_count must be non-negative")
        if self.provider_cost_eur < 0 or self.money_limit_eur < 0:
            raise ValueError("cost values must be non-negative")


def assess_image_asset_request(req: ImageAssetRequest) -> dict:
    req.validate()
    idempotency_key = f"ASSET_IMAGE_{req.run_id}"

    if req.existing_asset_count > 1:
        return {
            "status": "BLOCKED_DUPLICATES",
            "idempotency_key": idempotency_key,
            "reuse_existing": False,
            "generate_allowed": False,
            "external_action_allowed": False,
            "human_required": True,
            "human_reason": "HIGH_RISK",
            "legacy_scenario_must_remain_inactive": True,
            "old_preserved": True,
        }

    if req.existing_asset_count == 1:
        return {
            "status": "REUSE_EXISTING_ASSET",
            "idempotency_key": idempotency_key,
            "reuse_existing": True,
            "generate_allowed": False,
            "external_action_allowed": False,
            "human_required": False,
            "human_reason": None,
            "legacy_scenario_must_remain_inactive": True,
            "old_preserved": True,
        }

    if not req.paid_provider_enabled:
        return {
            "status": "QUEUED_ZERO_COST_PROVIDER_NOT_CONNECTED",
            "idempotency_key": idempotency_key,
            "reuse_existing": False,
            "generate_allowed": False,
            "external_action_allowed": False,
            "human_required": False,
            "human_reason": None,
            "additional_paid_ai_required": False,
            "legacy_scenario_must_remain_inactive": True,
            "old_preserved": True,
        }

    if req.provider_cost_eur > req.money_limit_eur:
        return {
            "status": "BLOCKED_MONEY_LIMIT",
            "idempotency_key": idempotency_key,
            "reuse_existing": False,
            "generate_allowed": False,
            "external_action_allowed": False,
            "human_required": True,
            "human_reason": "MONEY_LIMIT",
            "additional_paid_ai_required": False,
            "legacy_scenario_must_remain_inactive": True,
            "old_preserved": True,
        }

    return {
        "status": "PROVIDER_READY_BUT_EXECUTION_GATED",
        "idempotency_key": idempotency_key,
        "reuse_existing": False,
        "generate_allowed": False,
        "external_action_allowed": False,
        "human_required": req.environment == "PROD",
        "human_reason": "SIGNATURE_REQUIRED" if req.environment == "PROD" else None,
        "additional_paid_ai_required": False,
        "legacy_scenario_must_remain_inactive": True,
        "old_preserved": True,
    }
