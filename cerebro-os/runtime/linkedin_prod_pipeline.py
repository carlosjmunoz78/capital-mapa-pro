from dataclasses import dataclass
from typing import Any


LINKEDIN_PROD_TARGETS = {
    5554207: "text",
    9528327: "link",
    9522428: "image",
    9410589: "video",
}


@dataclass(frozen=True)
class LinkedInPublishRequest:
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
    authorized: bool
    content: str
    url: str = ""
    link_title: str = ""
    file_name: str = ""
    file_data_present: bool = False
    video_name: str = ""
    video_data_present: bool = False


def validate_linkedin_publish(req: LinkedInPublishRequest) -> dict:
    if req.scenario_id not in LINKEDIN_PROD_TARGETS:
        raise ValueError("unknown LinkedIn PROD target")
    blockers = []
    for name in ("company_id", "engine_id", "version", "publication_id", "run_id", "content"):
        if not str(getattr(req, name)).strip():
            blockers.append(f"MISSING_{name.upper()}")
    if req.environment != "PROD": blockers.append("ENVIRONMENT_NOT_PROD")
    if not req.engine_enabled: blockers.append("ENGINE_DISABLED")
    if not req.override_authorized_once: blockers.append("OVERRIDE_NOT_AUTHORIZED_ONCE")
    if not req.override_record_matches: blockers.append("OVERRIDE_RECORD_MISMATCH")
    if not req.idempotency_clear: blockers.append("DUPLICATE_OR_LOCK_PRESENT")
    if not req.authorized: blockers.append("SIGNATURE_REQUIRED")
    fmt = LINKEDIN_PROD_TARGETS[req.scenario_id]
    if fmt == "link" and (not req.url.strip() or not req.link_title.strip()): blockers.append("MISSING_LINK_CONTRACT")
    if fmt == "image" and (not req.file_name.strip() or not req.file_data_present): blockers.append("MISSING_IMAGE_BINARY")
    if fmt == "video" and (not req.video_name.strip() or not req.video_data_present): blockers.append("MISSING_VIDEO_BINARY")
    return {
        "scenario_id": req.scenario_id,
        "format": fmt,
        "status": "READY_FOR_EXPLICIT_EXECUTION" if not blockers else "BLOCKED",
        "blockers": tuple(blockers),
        "external_action_allowed": False,
        "requires_human": True if not blockers or "SIGNATURE_REQUIRED" in blockers else False,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers or "SIGNATURE_REQUIRED" in blockers else None,
    }


@dataclass(frozen=True)
class LinkedInReceiptInput:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    external_id: str
    notion_return_ok: bool


def normalize_linkedin_receipt(inp: LinkedInReceiptInput) -> dict:
    if inp.scenario_id not in LINKEDIN_PROD_TARGETS:
        raise ValueError("unknown LinkedIn PROD target")
    if inp.environment != "PROD":
        return _blocked_receipt(inp, "POLICY_CONFLICT")
    if not all((inp.company_id, inp.engine_id, inp.version, inp.publication_id, inp.run_id, inp.external_id)):
        return _blocked_receipt(inp, "LOW_CONFIDENCE")
    base = {
        "scenario_id": inp.scenario_id,
        "format": LINKEDIN_PROD_TARGETS[inp.scenario_id],
        "platform_state": "PUBLISHED",
        "receipt_status": "LINKEDIN_ACCEPTED",
        "external_id": inp.external_id,
        "external_action_allowed": False,
        "linkedin_called_by_runtime": False,
        "notion_mutation_allowed": False,
        "retry_publish_allowed": False,
    }
    if not inp.notion_return_ok:
        return {**base, "notion_state": "PENDING_RETURN", "idempotency_status": "LOCKED_PENDING_NOTION_RETURN", "override_status": "CONSUMED", "requires_human": False, "human_reason": None}
    return {**base, "notion_state": "Publicada", "idempotency_status": "COMMITTED", "override_status": "CONSUMED", "requires_human": False, "human_reason": None}


def _blocked_receipt(inp: LinkedInReceiptInput, reason: str) -> dict:
    return {
        "scenario_id": inp.scenario_id,
        "format": LINKEDIN_PROD_TARGETS.get(inp.scenario_id),
        "platform_state": "BLOCKED",
        "receipt_status": "BLOCKED",
        "idempotency_status": "BLOCKED",
        "override_status": "UNCHANGED",
        "external_action_allowed": False,
        "linkedin_called_by_runtime": False,
        "notion_mutation_allowed": False,
        "retry_publish_allowed": False,
        "requires_human": True,
        "human_reason": reason,
    }
