from dataclasses import dataclass
from typing import Optional


INSTAGRAM_MUTATORS = {
    9534139: "image",
    9534084: "carousel",
    9534087: "reel",
}


@dataclass(frozen=True)
class InstagramPublishInput:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    engine_enabled: bool
    override_authorized_once: bool
    override_record_matches: bool
    idempotency_clear: bool
    explicit_authorized: bool
    caption_present: bool
    image_url_present: bool = False
    video_url_present: bool = False
    files_count: Optional[int] = None
    share_to_feed_present: bool = False


@dataclass(frozen=True)
class InstagramReceiptInput:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    external_id: str
    permalink: str
    notion_return_ok: bool
    album_items_count: Optional[int] = None


def assess_instagram_publish(inp: InstagramPublishInput) -> dict:
    fmt = _format(inp.scenario_id)
    required = (inp.company_id, inp.engine_id, inp.environment, inp.version, inp.publication_id, inp.run_id)
    if any(not str(value).strip() for value in required):
        return _publish_block(inp, fmt, "MISSING_REQUIRED_SCOPE", "LOW_CONFIDENCE")
    if inp.environment != "PROD":
        return _publish_block(inp, fmt, "ENVIRONMENT_NOT_PROD", "POLICY_CONFLICT")

    gates = {
        "engine_enabled": inp.engine_enabled,
        "override_authorized_once": inp.override_authorized_once,
        "override_record_matches": inp.override_record_matches,
        "idempotency_clear": inp.idempotency_clear,
        "explicit_authorized": inp.explicit_authorized,
        "caption_present": inp.caption_present,
    }
    if fmt == "image":
        gates["image_url_present"] = inp.image_url_present
    elif fmt == "reel":
        gates["video_url_present"] = inp.video_url_present
        gates["share_to_feed_present"] = inp.share_to_feed_present
    elif fmt == "carousel":
        gates["files_count_2_10"] = inp.files_count is not None and 2 <= inp.files_count <= 10

    failed = tuple(name for name, ok in gates.items() if not ok)
    if failed:
        return {
            **_publish_base(inp, fmt),
            "status": "BLOCKED_INPUT_CONTRACT",
            "failed_gates": failed,
            "requires_human": "explicit_authorized" in failed or "override_authorized_once" in failed,
            "human_reason": "SIGNATURE_REQUIRED" if ("explicit_authorized" in failed or "override_authorized_once" in failed) else None,
        }

    return {
        **_publish_base(inp, fmt),
        "status": "READY_FOR_EXPLICIT_EXECUTION",
        "failed_gates": (),
        "requires_human": True,
        "human_reason": "SIGNATURE_REQUIRED",
    }


def normalize_instagram_receipt(inp: InstagramReceiptInput) -> dict:
    fmt = _format(inp.scenario_id)
    required = (inp.company_id, inp.engine_id, inp.environment, inp.version, inp.publication_id, inp.run_id, inp.external_id, inp.permalink)
    if any(not str(value).strip() for value in required):
        return _receipt_block(inp, fmt, "MISSING_REQUIRED_RECEIPT", "LOW_CONFIDENCE")
    if inp.environment != "PROD":
        return _receipt_block(inp, fmt, "RECEIPT_OUTSIDE_PROD", "POLICY_CONFLICT")
    if fmt == "carousel" and (inp.album_items_count is None or not 2 <= inp.album_items_count <= 10):
        return _receipt_block(inp, fmt, "CAROUSEL_ITEM_COUNT_MISMATCH", "LOW_CONFIDENCE")

    if not inp.notion_return_ok:
        return {
            **_receipt_base(inp, fmt),
            "status": "INSTAGRAM_CONFIRMED_NOTION_PENDING",
            "platform_state": "PUBLISHED",
            "notion_state": "PENDING_RETURN",
            "idempotency_state": "HOLD_UNTIL_NOTION_RETURN",
            "override_state": "MUST_CONSUME_AFTER_NOTION_RETURN",
            "requires_human": False,
            "human_reason": None,
        }

    return {
        **_receipt_base(inp, fmt),
        "status": "POST_PUBLISH_COMMITTED",
        "platform_state": "PUBLISHED",
        "notion_state": "Publicada",
        "idempotency_state": "COMMITTED",
        "override_state": "CONSUMED",
        "requires_human": False,
        "human_reason": None,
    }


def _format(scenario_id: int) -> str:
    try:
        return INSTAGRAM_MUTATORS[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown Instagram PROD mutator") from exc


def _publish_base(inp: InstagramPublishInput, fmt: str) -> dict:
    return {
        "scenario_id": inp.scenario_id,
        "format": fmt,
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "external_action_allowed": False,
        "instagram_mutation_allowed": False,
    }


def _publish_block(inp: InstagramPublishInput, fmt: str, status: str, reason: str) -> dict:
    return {
        **_publish_base(inp, fmt),
        "status": status,
        "failed_gates": (),
        "requires_human": True,
        "human_reason": reason,
    }


def _receipt_base(inp: InstagramReceiptInput, fmt: str) -> dict:
    return {
        "scenario_id": inp.scenario_id,
        "format": fmt,
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "external_id": inp.external_id,
        "permalink": inp.permalink,
        "external_action_allowed": False,
        "instagram_called_by_runtime": False,
        "notion_mutation_allowed": False,
        "retry_publish_allowed": False,
    }


def _receipt_block(inp: InstagramReceiptInput, fmt: str, status: str, reason: str) -> dict:
    return {
        **_receipt_base(inp, fmt),
        "status": status,
        "platform_state": "BLOCKED",
        "notion_state": "BLOCKED",
        "idempotency_state": "BLOCKED",
        "override_state": "UNCHANGED",
        "requires_human": True,
        "human_reason": reason,
    }
