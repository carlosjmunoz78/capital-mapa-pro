from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsCaptureRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    notion_record_id: str
    window: str
    post_id: str
    duplicate_committed: bool
    reactions: int = 0
    comments: int = 0
    shares: int = 0


def plan_analytics_capture(req: AnalyticsCaptureRequest) -> dict:
    if not all((req.company_id, req.engine_id, req.environment, req.version, req.notion_record_id, req.window)):
        raise ValueError("missing required analytics-capture scope")
    if req.window not in {"24h", "7d", "24H", "7D"}:
        raise ValueError("unsupported analytics window")
    if req.duplicate_committed:
        return {
            "status": "BLOCKED_DUPLICATE",
            "platform_state": "NOT_CALLED",
            "external_action_allowed": False,
            "notion_mutation_allowed": False,
            "learning_allowed": False,
            "requires_human": False,
        }
    if not req.post_id:
        return {
            "status": "BLOCKED_POST_ID_MISSING",
            "platform_state": "NOT_CALLED",
            "external_action_allowed": False,
            "notion_mutation_allowed": False,
            "learning_allowed": False,
            "requires_human": True,
            "human_reason": "LOW_CONFIDENCE",
        }
    if min(req.reactions, req.comments, req.shares) < 0:
        raise ValueError("analytics metrics cannot be negative")
    result_hash = f"REACTIONS_{req.reactions}|COMMENTS_{req.comments}|SHARES_{req.shares}|TIMEZONE_OK"
    return {
        "status": "CAPTURED_PARTIAL",
        "platform_state": "POST_FOUND",
        "external_action_allowed": False,
        "notion_mutation_allowed": False,
        "learning_allowed": False,
        "quality_status": "PARTIAL_DATA_REVIEW",
        "reconciliation_status": "CONSISTENT_CAPTURED_PARTIAL_HOLD",
        "idempotency_status": "COMMITTED",
        "window_status": "CLOSED_CAPTURED_PARTIAL",
        "requires_human": True,
        "human_reason": "LOW_CONFIDENCE",
        "result_hash": result_hash,
    }
