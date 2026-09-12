from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FacebookV4InputEvidence:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    technical_format_ok: bool
    production_final: bool
    final_approved: bool
    production_gate_ok: bool
    incoherence_absent: bool
    brand_qa_approved: bool
    legal_qa_ok: bool
    copy_present: bool
    channel_facebook_social: bool
    supervisor_ready: bool
    schedule_programmed: bool
    schedule_due: bool
    schedule_incident_absent: bool
    run_ids_match: bool
    integration_unblocked: bool
    copy_reviewed: bool
    authorization_once: bool
    override_record_matches: bool
    override_not_expired: bool
    idempotency_clear: bool
    t48_approved: bool = False
    t48_date_valid: bool = False
    t48_version_locked: bool = False
    t48_hash_present: bool = False
    final_url_present: bool = False
    utm_required: bool = False
    domain_allowed: bool = False
    asset_approved: bool = False
    asset_principal: bool = False
    asset_type: Optional[str] = None
    asset_brand_qa_approved: bool = False
    asset_legal_qa_ok: bool = False
    orientation: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    mime: Optional[str] = None
    photo_count: Optional[int] = None
    explicit_authorized: bool = False


_T48_FORMATS = {"text", "link", "image"}


def validate_v4_input_contract(inp: FacebookV4InputEvidence) -> dict:
    required_scope = (inp.company_id, inp.engine_id, inp.environment, inp.version, inp.publication_id, inp.run_id, inp.format)
    if any(not str(value).strip() for value in required_scope):
        return _blocked(inp, "MISSING_REQUIRED_SCOPE", "LOW_CONFIDENCE")
    if inp.environment != "PROD":
        return _blocked(inp, "ENVIRONMENT_NOT_PROD", "POLICY_CONFLICT")

    supported = {"text", "link", "image", "reel", "carousel", "video_long"}
    if inp.format not in supported:
        return _blocked(inp, "UNSUPPORTED_FORMAT", "LOW_CONFIDENCE")

    common = {
        "technical_format_ok": inp.technical_format_ok,
        "production_final": inp.production_final,
        "final_approved": inp.final_approved,
        "production_gate_ok": inp.production_gate_ok,
        "incoherence_absent": inp.incoherence_absent,
        "brand_qa_approved": inp.brand_qa_approved,
        "legal_qa_ok": inp.legal_qa_ok,
        "copy_present": inp.copy_present,
        "channel_facebook_social": inp.channel_facebook_social,
        "supervisor_ready": inp.supervisor_ready,
        "schedule_programmed": inp.schedule_programmed,
        "schedule_due": inp.schedule_due,
        "schedule_incident_absent": inp.schedule_incident_absent,
        "run_ids_match": inp.run_ids_match,
        "integration_unblocked": inp.integration_unblocked,
        "copy_reviewed": inp.copy_reviewed,
        "authorization_once": inp.authorization_once,
        "override_record_matches": inp.override_record_matches,
        "override_not_expired": inp.override_not_expired,
        "idempotency_clear": inp.idempotency_clear,
    }
    failed = [name for name, ok in common.items() if not ok]

    if inp.format in _T48_FORMATS:
        t48 = {
            "t48_approved": inp.t48_approved,
            "t48_date_valid": inp.t48_date_valid,
            "t48_version_locked": inp.t48_version_locked,
            "t48_hash_present": inp.t48_hash_present,
        }
        failed.extend(name for name, ok in t48.items() if not ok)

    if inp.format == "link":
        if not inp.final_url_present:
            failed.append("final_url_present")
        if not inp.utm_required:
            failed.append("utm_required")
        if not inp.domain_allowed:
            failed.append("domain_allowed")

    if inp.format in {"image", "reel"}:
        asset = {
            "asset_approved": inp.asset_approved,
            "asset_principal": inp.asset_principal,
            "asset_brand_qa_approved": inp.asset_brand_qa_approved,
            "asset_legal_qa_ok": inp.asset_legal_qa_ok,
        }
        failed.extend(name for name, ok in asset.items() if not ok)

    if inp.format == "image" and inp.asset_type != "Imagen":
        failed.append("asset_type_image")

    if inp.format == "reel":
        if inp.asset_type != "Vídeo":
            failed.append("asset_type_video")
        if inp.orientation != "Vertical":
            failed.append("orientation_vertical")
        if inp.width is None or inp.width < 540:
            failed.append("width_min_540")
        if inp.height is None or inp.height < 960:
            failed.append("height_min_960")
        if inp.duration_seconds is None or not (3 <= inp.duration_seconds <= 90):
            failed.append("duration_3_90")
        if inp.mime != "video/mp4":
            failed.append("mime_video_mp4")

    if inp.format == "carousel":
        if inp.photo_count is None or not (2 <= inp.photo_count <= 30):
            failed.append("photo_count_2_30")
        if not inp.explicit_authorized:
            failed.append("explicit_authorized")

    if inp.format == "video_long" and not inp.explicit_authorized:
        failed.append("explicit_authorized")

    if failed:
        return {
            **_base(inp),
            "status": "BLOCKED_INPUT_CONTRACT",
            "failed_gates": tuple(sorted(set(failed))),
            "requires_human": "authorization_once" in failed or "explicit_authorized" in failed,
            "human_reason": "SIGNATURE_REQUIRED" if ("authorization_once" in failed or "explicit_authorized" in failed) else None,
        }

    return {
        **_base(inp),
        "status": "INPUT_CONTRACT_GREEN",
        "failed_gates": (),
        "requires_human": True,
        "human_reason": "SIGNATURE_REQUIRED",
    }


def _base(inp: FacebookV4InputEvidence) -> dict:
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
    }


def _blocked(inp: FacebookV4InputEvidence, status: str, reason: str) -> dict:
    return {
        **_base(inp),
        "status": status,
        "failed_gates": (),
        "requires_human": True,
        "human_reason": reason,
    }
