from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class DispatchCandidate:
    company_id: str
    engine_id: str
    environment: str
    version: str
    notion_record_id: str
    run_id: str
    platform: str
    technical_format: str
    publication_state: str
    integration_blocked: bool
    has_programming_relation: bool
    has_production_order: bool
    t48_approved: bool
    t48_approval_date_present: bool
    t48_locked_version_present: bool
    t48_hash_present: bool
    real_publication_authorization: str

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.notion_record_id, self.run_id, self.platform, self.technical_format, self.publication_state)
        if any(not str(v).strip() for v in required):
            raise ValueError("dispatch candidate missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")


def classify_candidate(candidate: DispatchCandidate) -> dict:
    candidate.validate()
    eligible = (
        candidate.publication_state == "Pendiente de publicar"
        and not candidate.integration_blocked
        and candidate.has_programming_relation
        and candidate.has_production_order
        and candidate.t48_approved
        and candidate.t48_approval_date_present
        and candidate.t48_locked_version_present
        and candidate.t48_hash_present
    )
    return {
        "company_id": candidate.company_id,
        "engine_id": candidate.engine_id,
        "environment": candidate.environment,
        "version": candidate.version,
        "notion_record_id": candidate.notion_record_id,
        "run_id": candidate.run_id,
        "network": candidate.platform,
        "operation_type": f"dispatch_{candidate.technical_format}",
        "status": "ROUTE_PREPARED_ENGINE_OFF" if eligible else "BLOCKED_NOT_ELIGIBLE",
        "platform_state": "NOT_CALLED",
        "requires_human": True,
        "external_action_allowed": False,
        "publication_authorization": candidate.real_publication_authorization,
    }


def summarize_query(candidate_count: int, *, company_id: str, engine_id: str, environment: str, version: str) -> dict:
    if candidate_count < 0:
        raise ValueError("candidate_count must be non-negative")
    if environment not in VALID_ENVIRONMENTS or not all(str(v).strip() for v in (company_id, engine_id, version)):
        raise ValueError("invalid dispatcher scope")
    return {
        "company_id": company_id,
        "engine_id": engine_id,
        "environment": environment,
        "version": version,
        "candidate_count": candidate_count,
        "status": "CANDIDATES_CLASSIFIED_NO_EXECUTION",
        "platform_state": "NO_PLATFORM_CALLED",
        "external_action_allowed": False,
    }
