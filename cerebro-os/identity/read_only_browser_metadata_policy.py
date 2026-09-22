from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

_ALLOWED_URL = "https://example.com/"
_ALLOWED_ACTION = "READ_ONLY_PAGE_METADATA"


@dataclass(frozen=True)
class BrowserMetadataRequest:
    company_id: str
    device_id: str
    environment: str
    version: str
    action: str
    target_url: str
    policy_green: bool
    bridge_online: bool
    extension_fresh: bool
    higher_priority_connector: bool = False


def plan_read_only_metadata(request: BrowserMetadataRequest) -> dict:
    """Define the only permitted pilot navigation; this does not dispatch it."""
    if not all((request.company_id, request.device_id, request.environment,
                request.version, request.action, request.target_url)):
        raise ValueError("navigation scope required")
    blockers = []
    if request.company_id != "fenix" or request.environment != "LAB" or request.version != "v0":
        blockers.append("PILOT_SCOPE_REQUIRED")
    if request.action != _ALLOWED_ACTION or request.target_url != _ALLOWED_URL:
        blockers.append("URL_OR_ACTION_NOT_ALLOWLISTED")
    if request.higher_priority_connector:
        blockers.append("USE_HIGHER_PRIORITY_CONNECTOR")
    if not request.bridge_online or not request.extension_fresh:
        blockers.append("LIVE_BRIDGE_REQUIRED")
    if not request.policy_green:
        blockers.append("POLICY_NOT_GREEN")
    return {
        "record_type": "onb_gap_read_only_browser_plan",
        "company_id": request.company_id,
        "device_id": request.device_id,
        "engine_id": "ONB-GAP-001",
        "environment": request.environment,
        "version": request.version,
        "status": "GREEN" if not blockers else "BLOCKED",
        "decision": "ALLOW_PILOT_METADATA_ONLY" if not blockers else "DO_NOT_DISPATCH",
        "blockers": tuple(blockers),
        "allowed_url": _ALLOWED_URL if not blockers else None,
        "allowed_action": _ALLOWED_ACTION if not blockers else None,
        "page_content_access": False,
        "form_interaction": False,
        "credential_access": False,
        "external_mutation_allowed": False,
        "prod_activation_allowed": False,
        "requires_extension_upgrade": True,
        "cost_eur": 0.0,
    }


def verify_page_metadata(plan: dict, receipt: dict) -> dict:
    """Never conflate tab creation with a verified successful navigation."""
    allowed = (
        plan.get("status") == "GREEN"
        and plan.get("decision") == "ALLOW_PILOT_METADATA_ONLY"
        and plan.get("allowed_url") == _ALLOWED_URL
        and receipt.get("status") == "COMPLETED"
        and receipt.get("requested_url") == _ALLOWED_URL
        and receipt.get("observed_url") == _ALLOWED_URL
        and receipt.get("observed_title") == "Example Domain"
        and receipt.get("page_load_complete") is True
        and receipt.get("external_mutation_performed") is False
        and receipt.get("secret_value_included") is False
        and receipt.get("page_content_included") is False
    )
    # An unapproved redirect or an observed title mismatch is never semantically green.
    return {
        "engine_id": "ONB-GAP-001",
        "status": "GREEN" if allowed else "PARTIAL",
        "semantic_verified": bool(allowed),
        "decision": "READ_ONLY_PAGE_METADATA_VERIFIED" if allowed else "READBACK_REQUIRED",
        "external_mutation_allowed": False,
        "prod_activation_allowed": False,
        "cost_eur": 0.0,
    }
