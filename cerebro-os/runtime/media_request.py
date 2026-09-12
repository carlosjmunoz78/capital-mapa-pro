from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_PRIORITIES = {"LOW", "NORMAL", "HIGH", "URGENT"}


@dataclass(frozen=True)
class MediaRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    run_id: str
    production_order_id: str
    network: str
    format: str
    image_count: int
    needs_voice: bool
    needs_presenter: bool
    needs_video: bool
    needs_editing: bool
    priority: str

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.run_id, self.production_order_id, self.network, self.format, self.priority)
        if any(not str(v).strip() for v in required):
            raise ValueError("media request missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.image_count < 0:
            raise ValueError("image_count must be non-negative")
        if self.priority.upper() not in VALID_PRIORITIES:
            raise ValueError("invalid priority")


def plan_media_request(req: MediaRequest, *, paid_provider_connected: bool = False) -> dict:
    req.validate()
    needs_any_provider = any((req.image_count > 0, req.needs_voice, req.needs_presenter, req.needs_video, req.needs_editing))
    if needs_any_provider and not paid_provider_connected:
        status = "BLOCKED_BY_COST"
        provider_status = "QUEUED_PROVIDERS_NOT_CONNECTED"
        external_action_allowed = False
    else:
        status = "READY_FOR_RUNTIME"
        provider_status = "NO_PROVIDER_REQUIRED" if not needs_any_provider else "PROVIDER_AVAILABLE"
        external_action_allowed = False
    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "run_id": req.run_id,
        "production_order_id": req.production_order_id,
        "network": req.network,
        "format": req.format,
        "priority": req.priority.upper(),
        "status": status,
        "provider_status": provider_status,
        "requires_human": status == "BLOCKED_BY_COST",
        "external_action_allowed": external_action_allowed,
    }
