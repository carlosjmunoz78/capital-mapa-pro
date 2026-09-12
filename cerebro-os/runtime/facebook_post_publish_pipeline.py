from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from facebook_analytics_windows import AnalyticsWindowsRequest, plan_analytics_windows
from facebook_post_publish_state import PostPublishInput, evaluate_post_publish
from facebook_publish_receipt import ReceiptInput, normalize_receipt


@dataclass(frozen=True)
class FacebookPostPublishPipelineInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    external_id: str
    published_at: str
    permalink: Optional[str] = None
    photo_id: Optional[str] = None
    platform_confirmed: bool = True
    notion_return_ok: bool = False
    override_consumed: bool = False
    idempotency_committed: bool = False
    canonical_receipt_exists: bool = False
    windows_exist: bool = False


def evaluate_facebook_post_publish_pipeline(inp: FacebookPostPublishPipelineInput) -> dict:
    """Compose receipt, post-publish state, and analytics-window planning.

    This is intentionally decision-only. It cannot call Facebook, mutate Notion,
    consume overrides, commit provider-side idempotency, or create analytics windows.
    """
    receipt = normalize_receipt(
        ReceiptInput(
            company_id=inp.company_id,
            engine_id=inp.engine_id,
            environment=inp.environment,
            version=inp.version,
            publication_id=inp.publication_id,
            run_id=inp.run_id,
            format=inp.format,
            external_id=inp.external_id,
            permalink=inp.permalink,
            photo_id=inp.photo_id,
            notion_return_ok=inp.notion_return_ok,
            platform_confirmed=inp.platform_confirmed,
        )
    )

    if receipt.get("requires_human"):
        return _blocked(inp, receipt.get("human_reason"), receipt.get("receipt_status"), receipt)

    post = evaluate_post_publish(
        PostPublishInput(
            company_id=inp.company_id,
            engine_id=inp.engine_id,
            environment=inp.environment,
            version=inp.version,
            publication_id=inp.publication_id,
            run_id=inp.run_id,
            receipt_confirmed=inp.platform_confirmed,
            notion_return_ok=inp.notion_return_ok,
            override_consumed=inp.override_consumed,
            idempotency_committed=inp.idempotency_committed,
            platform_state=receipt.get("platform_state", "UNKNOWN"),
        )
    )

    if post.get("human_required"):
        return {
            **_base(inp),
            "pipeline_state": post["state"],
            "receipt": receipt,
            "post_publish": post,
            "analytics": None,
            "analytics_windows_ready": False,
            "requires_human": True,
            "human_reason": post.get("human_reason"),
        }

    if post.get("state") != "POST_PUBLISH_COMMITTED":
        return {
            **_base(inp),
            "pipeline_state": post["state"],
            "receipt": receipt,
            "post_publish": post,
            "analytics": None,
            "analytics_windows_ready": False,
            "requires_human": False,
            "human_reason": None,
        }

    canonical_ready = bool(inp.canonical_receipt_exists or receipt.get("receipt_status") == "FACEBOOK_ACCEPTED")
    analytics = plan_analytics_windows(
        AnalyticsWindowsRequest(
            company_id=inp.company_id,
            engine_id=inp.engine_id,
            environment=inp.environment,
            version=inp.version,
            publication_id=inp.publication_id,
            external_id=inp.external_id,
            published_at=inp.published_at,
            canonical_receipt_exists=canonical_ready,
            windows_exist=inp.windows_exist,
        )
    )

    return {
        **_base(inp),
        "pipeline_state": "POST_PUBLISH_COMMITTED",
        "receipt": receipt,
        "post_publish": post,
        "analytics": analytics,
        "analytics_windows_ready": analytics.get("status") == "WINDOWS_READY_TO_CREATE",
        "requires_human": bool(analytics.get("requires_human", False)),
        "human_reason": analytics.get("human_reason"),
    }


def _base(inp: FacebookPostPublishPipelineInput) -> dict:
    return {
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "format": inp.format,
        "external_action_allowed": False,
        "facebook_mutation_allowed": False,
        "notion_mutation_allowed": False,
        "retry_publish_allowed": False,
    }


def _blocked(inp: FacebookPostPublishPipelineInput, reason: Optional[str], state: Optional[str], receipt: dict) -> dict:
    return {
        **_base(inp),
        "pipeline_state": state or "BLOCKED",
        "receipt": receipt,
        "post_publish": None,
        "analytics": None,
        "analytics_windows_ready": False,
        "requires_human": True,
        "human_reason": reason or "LOW_CONFIDENCE",
    }
