from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class VideoLongPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    video_url: str
    mime: str
    duration_seconds: float
    width: int
    height: int
    qa_approved: bool
    real_publish_authorized: bool
    http_status: int

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.publication_id, self.run_id, self.video_url, self.mime)
        if any(not str(value).strip() for value in required):
            raise ValueError("video long preflight missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.duration_seconds <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("invalid media dimensions or duration")


def evaluate_video_long_preflight(req: VideoLongPreflightRequest) -> dict:
    req.validate()
    http_ok = 200 <= req.http_status < 400
    contract_ok = http_ok and req.duration_seconds > 90 and req.qa_approved and not req.real_publish_authorized
    status = "DIRECT_CONTRACT_VALIDATED" if contract_ok else "BLOCKED_PREFLIGHT"
    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "status": status,
        "operation_type": "video_long_preflight",
        "platform_state": "FACEBOOK_NOT_CALLED",
        "requires_human": False if contract_ok else True,
        "external_action_allowed": False,
        "http_ok": http_ok,
        "duration_seconds": req.duration_seconds,
        "qa_approved": req.qa_approved,
        "real_publish_authorized": req.real_publish_authorized,
    }
