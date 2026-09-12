from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class YouTubeProcessingObservation:
    company_id: str
    engine_id: str
    environment: str
    version: str
    run_id: str
    publication_id: str
    video_id: str
    http_status: int
    upload_status: str
    qa_approved: bool = False

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.environment,
            self.version,
            self.run_id,
            self.publication_id,
            self.video_id,
            self.upload_status,
        )
        if any(not str(value).strip() for value in required):
            raise ValueError("youtube processing observation missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.http_status < 100 or self.http_status > 599:
            raise ValueError("invalid http status")


def classify_processing(obs: YouTubeProcessingObservation) -> dict:
    """Pure classification of the Make 9537708 observation contract.

    This function never calls YouTube. A connector/edge may supply the observed
    API state, while CEREBRO owns the deterministic interpretation and policy.
    OLD Make behavior is preserved: the observation is PROCESSING_READ and a
    human gate remains present until READY/processed plus QA evidence exists.
    """
    obs.validate()
    normalized = obs.upload_status.strip().lower()
    ready = normalized in {"processed", "ready"} and obs.qa_approved and 200 <= obs.http_status < 400

    return {
        "company_id": obs.company_id,
        "engine_id": obs.engine_id,
        "environment": obs.environment,
        "version": obs.version,
        "run_id": obs.run_id,
        "publication_id": obs.publication_id,
        "video_id": obs.video_id,
        "status": "PROCESSING_READ",
        "network": "YouTube",
        "operation_type": "verify_video_processing",
        "platform_state": obs.upload_status,
        "http_status": obs.http_status,
        "qa_approved": obs.qa_approved,
        "ready_for_next_gate": ready,
        "requires_human": not ready,
        "external_action_allowed": False,
        "connector_action_required": False,
    }
