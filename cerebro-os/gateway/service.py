from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayRequest:
    company_id: str
    engine_id: str
    capability: str
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not self.company_id or not self.engine_id or not self.capability or not self.version:
            raise ValueError("company_id, engine_id, capability and version are required")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")


class Gateway:
    def __init__(self, engine_ids: set[str], connector_registry, policy_check=None):
        self.engine_ids = set(engine_ids)
        self.connector_registry = connector_registry
        self.policy_check = policy_check or (lambda request: (True, None))

    def route(self, request: GatewayRequest) -> dict:
        request.validate()
        if request.engine_id not in self.engine_ids:
            return {"status": "HUMAN_REQUIRED", "reason": "LOW_CONFIDENCE"}
        allowed, reason = self.policy_check(request)
        if not allowed:
            return {"status": "HUMAN_REQUIRED", "reason": reason or "POLICY_CONFLICT"}
        connector = self.connector_registry.route(request.capability, request.company_id, request.environment)
        if connector is None:
            return {"status": "HUMAN_REQUIRED", "reason": "LOW_CONFIDENCE"}
        return {
            "status": "ROUTED",
            "company_id": request.company_id,
            "engine_id": request.engine_id,
            "connector_id": connector.connector_id,
            "route_type": connector.route_type,
            "environment": request.environment,
            "version": request.version,
        }
