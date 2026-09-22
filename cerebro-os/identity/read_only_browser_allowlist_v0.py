"""Future browser expansion contract. Side-effect-free; never dispatches commands.

Pilot v1.5 remains fixed at https://example.com/. This module is an
additional fail-closed planner, NOT a browser executor or PROD permission.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class AllowlistPolicy:
    company_id: str
    environment: str
    version: str
    allowed_origins: tuple[str, ...]
    connector_available: bool
    user_approved_origins: bool
    bridge_online: bool
    extension_fresh: bool
    change_control_green: bool


def _exact_origin(raw: str) -> str | None:
    """Only canonical public HTTPS origins, never credentials or IP literals."""
    try:
        parsed = urlsplit(raw)
        host = (parsed.hostname or "").lower()
        if (parsed.scheme != "https" or not host or parsed.username is not None
                or parsed.password is not None or parsed.port is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or raw != f"https://{host}/"):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        if host == "localhost" or host.endswith(".localhost") or not all(
            part and part[0].isalnum() and part[-1].isalnum()
            and all(c.isalnum() or c == "-" for c in part)
            for part in host.split(".")
        ):
            return None
        if len(host) > 253 or "." not in host:
            return None
        return f"https://{host}/"
    except (ValueError, AttributeError):
        return None


def plan_public_metadata_navigation(policy: AllowlistPolicy, target_url: str) -> dict:
    blockers: list[str] = []
    origin = _exact_origin(target_url)
    allowed = tuple(_exact_origin(x) for x in policy.allowed_origins)
    if policy.company_id != "fenix" or policy.environment != "LAB" or policy.version != "v0":
        blockers.append("LAB_PILOT_SCOPE_REQUIRED")
    if not origin or origin not in allowed or None in allowed:
        blockers.append("ORIGIN_NOT_EXACTLY_ALLOWLISTED")
    if policy.connector_available:
        blockers.append("CONNECTOR_FIRST")
    if not policy.user_approved_origins:
        blockers.append("EXPLICIT_ORIGIN_APPROVAL_REQUIRED")
    if not policy.bridge_online or not policy.extension_fresh:
        blockers.append("LIVE_EXTENSION_REQUIRED")
    if not policy.change_control_green:
        blockers.append("CHANGE_CONTROL_REQUIRED")
    # v1.5 can navigate only to the exact fixed test URL.
    # Enabling any other target requires reviewed new extension + transport +
    # local-service implementations and a successful physical PREPROD pilot.
    if origin != "https://example.com/":
        blockers.append("RUNTIME_NOT_IMPLEMENTED_FOR_TARGET")
    return {
        "record_type": "onb_gap_public_metadata_allowlist_plan",
        "company_id": policy.company_id,
        "engine_id": "ONB-GAP-001",
        "environment": policy.environment,
        "version": policy.version,
        "status": "GREEN" if not blockers else "BLOCKED",
        "decision": "ALLOW_EXISTING_FIXED_METADATA_PILOT" if not blockers else "DO_NOT_DISPATCH",
        "target_url": origin if not blockers else None,
        "blockers": tuple(blockers),
        "redirect_policy": "DENY",
        "page_content_access": False,
        "cookie_access": False,
        "form_interaction": False,
        "external_mutation_allowed": False,
        "prod_activation_allowed": False,
        "cost_eur": 0.0,
    }
