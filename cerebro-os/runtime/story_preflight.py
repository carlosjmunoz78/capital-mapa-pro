from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class StoryRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    asset_type: str
    asset_url: str
    width: float
    height: float
    qa_approved: bool
    duration_seconds: float | None = None

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.publication_id, self.run_id, self.asset_type, self.asset_url)
        if any(not str(v).strip() for v in required):
            raise ValueError("story request missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("invalid dimensions")


def preflight_story(req: StoryRequest) -> dict:
    req.validate()
    vertical = req.height > req.width
    ready = vertical and req.qa_approved and bool(req.asset_url.strip())
    if not ready:
        return {
            "company_id": req.company_id,
            "engine_id": req.engine_id,
            "environment": req.environment,
            "version": req.version,
            "publication_id": req.publication_id,
            "run_id": req.run_id,
            "status": "BLOCKED_PREFLIGHT",
            "requires_human": True,
            "external_action_allowed": False,
        }
    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "status": "BLOCKED_PROVIDER_NOT_CONNECTED",
        "preflight_status": "READY_FOR_PROVIDER_OR_MANUAL_HANDOFF",
        "provider_state": "NATIVE_CONNECTOR_UNAVAILABLE",
        "requires_human": True,
        "external_action_allowed": False,
    }
