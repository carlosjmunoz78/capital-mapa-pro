from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class AnalyticsWindowsRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    external_id: str
    published_at: str
    canonical_receipt_exists: bool
    windows_exist: bool


def plan_analytics_windows(req: AnalyticsWindowsRequest) -> dict:
    if not all((req.company_id, req.engine_id, req.environment, req.version, req.publication_id)):
        raise ValueError("missing required analytics-window scope")
    if req.windows_exist:
        return {
            "status": "BLOCKED_EXISTING_WINDOWS",
            "external_action_allowed": False,
            "notion_mutation_allowed": False,
            "requires_human": False,
        }
    if not req.canonical_receipt_exists:
        return {
            "status": "WAITING_PUBLICATION_RECEIPT",
            "external_action_allowed": False,
            "notion_mutation_allowed": False,
            "requires_human": True,
            "human_reason": "LOW_CONFIDENCE",
        }
    if not req.external_id or not req.published_at:
        raise ValueError("canonical receipt missing external id or publication time")
    published = datetime.fromisoformat(req.published_at.replace("Z", "+00:00"))
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return {
        "status": "WINDOWS_READY_TO_CREATE",
        "external_action_allowed": False,
        "notion_mutation_allowed": False,
        "requires_human": False,
        "window_24h_at": (published + timedelta(hours=24)).astimezone(timezone.utc).isoformat(),
        "window_24h_grace_until": (published + timedelta(hours=27)).astimezone(timezone.utc).isoformat(),
        "window_7d_at": (published + timedelta(days=7)).astimezone(timezone.utc).isoformat(),
        "window_7d_grace_until": (published + timedelta(days=7, hours=3)).astimezone(timezone.utc).isoformat(),
        "idempotency_key": f"FACEBOOK|ANALYTICS_WINDOWS|{req.publication_id}",
    }
