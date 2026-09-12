from dataclasses import dataclass

ALLOWED_KINDS = {"reel", "video_long"}

@dataclass(frozen=True)
class VideoFinalizerInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    kind: str
    external_id: str
    published: bool
    platform_status: str
    permalink_url: str | None = None
    first_seen_at: str | None = None
    lock_until: str | None = None


def finalize_video(inp: VideoFinalizerInput) -> dict:
    required = [inp.company_id, inp.engine_id, inp.environment, inp.version, inp.publication_id, inp.run_id, inp.external_id]
    if not all(required):
        return _blocked(inp, "LOW_CONFIDENCE", "MISSING_REQUIRED_SCOPE_OR_ID")
    if inp.environment != "PROD":
        return _blocked(inp, "POLICY_CONFLICT", "PROD_RECEIPT_OUTSIDE_PROD")
    if inp.kind not in ALLOWED_KINDS:
        return _blocked(inp, "LOW_CONFIDENCE", "UNKNOWN_VIDEO_KIND")

    permalink = (inp.permalink_url or "").strip()
    status = (inp.platform_status or "").strip().lower()

    if inp.kind == "reel":
        confirmed = inp.published is True and bool(permalink)
    else:
        confirmed = inp.published is True and status == "ready"

    if confirmed:
        return {
            "company_id": inp.company_id,
            "engine_id": inp.engine_id,
            "environment": inp.environment,
            "version": inp.version,
            "publication_id": inp.publication_id,
            "run_id": inp.run_id,
            "kind": inp.kind,
            "external_id": inp.external_id,
            "state": "PUBLISHED_CONFIRMED",
            "platform_state": "PUBLISHED",
            "canonical_receipt_ready": True,
            "notion_return_ready": True,
            "idempotency_state": "COMMIT_AFTER_NOTION_RETURN",
            "analytics_windows_ready_after_commit": True,
            "retry_upload_allowed": False,
            "poll_only": False,
            "external_action_allowed": False,
            "facebook_mutation_allowed": False,
            "notion_mutation_allowed": False,
            "permalink_url": permalink or None,
            "human_required": False,
            "human_reason": None,
        }

    return {
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "kind": inp.kind,
        "external_id": inp.external_id,
        "state": "PLATFORM_PROCESSING",
        "platform_state": status.upper() if status else "PROCESSING",
        "canonical_receipt_ready": False,
        "notion_return_ready": False,
        "idempotency_state": "PENDING_PLATFORM_CONFIRMATION",
        "analytics_windows_ready_after_commit": False,
        "retry_upload_allowed": False,
        "poll_only": True,
        "external_action_allowed": False,
        "facebook_mutation_allowed": False,
        "notion_mutation_allowed": False,
        "permalink_url": permalink or None,
        "human_required": False,
        "human_reason": None,
    }


def _blocked(inp: VideoFinalizerInput, reason: str, state: str) -> dict:
    return {
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "kind": inp.kind,
        "external_id": inp.external_id,
        "state": state,
        "platform_state": "NOT_CALLED",
        "canonical_receipt_ready": False,
        "notion_return_ready": False,
        "idempotency_state": "BLOCKED",
        "analytics_windows_ready_after_commit": False,
        "retry_upload_allowed": False,
        "poll_only": False,
        "external_action_allowed": False,
        "facebook_mutation_allowed": False,
        "notion_mutation_allowed": False,
        "permalink_url": None,
        "human_required": True,
        "human_reason": reason,
    }
