from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


SUPPORTED_FORMATS = {
    "text": "POST",
    "link": "POST",
    "image": "POST",
    "reel": "VIDEO",
    "carousel": "POST",
    "video_long": "VIDEO",
}


@dataclass(frozen=True)
class ReceiptInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    external_id: str
    permalink: Optional[str] = None
    photo_id: Optional[str] = None
    notion_return_ok: bool = False
    platform_confirmed: bool = True


def normalize_receipt(data: ReceiptInput) -> dict:
    """Normalize OLD Make Facebook receipts without performing external mutations.

    This function represents the post-platform state only. It cannot call Facebook,
    Notion, Make, or any external provider.
    """
    required = (
        data.company_id,
        data.engine_id,
        data.environment,
        data.version,
        data.publication_id,
        data.run_id,
        data.external_id,
    )
    if not all(required):
        return _blocked(data, "LOW_CONFIDENCE", "MISSING_REQUIRED_SCOPE_OR_RECEIPT")
    if data.environment != "PROD":
        return _blocked(data, "POLICY_CONFLICT", "PROD_RECEIPT_OUTSIDE_PROD")
    if data.format not in SUPPORTED_FORMATS:
        return _blocked(data, "LOW_CONFIDENCE", "UNSUPPORTED_FORMAT")

    base = {
        "company_id": data.company_id,
        "engine_id": data.engine_id,
        "environment": data.environment,
        "version": data.version,
        "publication_id": data.publication_id,
        "run_id": data.run_id,
        "format": data.format,
        "external_id": data.external_id,
        "platform_state": "PUBLISHED" if data.platform_confirmed else "UPLOAD_ACCEPTED",
        "external_action_allowed": False,
        "facebook_called_by_runtime": False,
        "notion_mutation_allowed": False,
    }

    if data.format in {"reel", "video_long"} and not data.platform_confirmed:
        return {
            **base,
            "receipt_status": "VIDEO_PROCESSING" if data.format == "video_long" else "FACEBOOK_UPLOAD_ACCEPTED_PROCESSING",
            "idempotency_status": "PENDING_PLATFORM_CONFIRMATION",
            "override_status": "CONSUMED",
            "notion_state": "Pendiente de publicar",
            "analytics_windows_ready": False,
            "requires_human": False,
            "human_reason": None,
        }

    if not data.notion_return_ok:
        return {
            **base,
            "receipt_status": "FACEBOOK_ACCEPTED",
            "idempotency_status": "LOCKED_PENDING_NOTION_RETURN",
            "override_status": "CONSUMED",
            "notion_state": "PENDING_RETURN",
            "analytics_windows_ready": False,
            "requires_human": False,
            "human_reason": None,
        }

    return {
        **base,
        "receipt_status": "FACEBOOK_ACCEPTED",
        "idempotency_status": "COMMITTED",
        "override_status": "CONSUMED",
        "notion_state": "Publicada",
        "analytics_windows_ready": True,
        "requires_human": False,
        "human_reason": None,
        "permalink": data.permalink,
        "photo_id": data.photo_id,
    }


def _blocked(data: ReceiptInput, reason: str, status: str) -> dict:
    return {
        "company_id": data.company_id,
        "engine_id": data.engine_id,
        "environment": data.environment,
        "version": data.version,
        "publication_id": data.publication_id,
        "run_id": data.run_id,
        "format": data.format,
        "receipt_status": status,
        "idempotency_status": "BLOCKED",
        "override_status": "UNCHANGED",
        "analytics_windows_ready": False,
        "external_action_allowed": False,
        "facebook_called_by_runtime": False,
        "notion_mutation_allowed": False,
        "requires_human": True,
        "human_reason": reason,
    }
