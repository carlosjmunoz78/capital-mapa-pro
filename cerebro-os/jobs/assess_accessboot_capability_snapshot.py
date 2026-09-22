from __future__ import annotations

from datetime import datetime, timezone


def assess_snapshot(command: dict, *, company_id: str, device_id: str, now: datetime) -> dict:
    """Assess a scoped, fresh LAB snapshot without copying profile names."""
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    result = command.get("result")
    if not isinstance(result, dict):
        raise ValueError("snapshot result required")
    for row in (command, result):
        if row.get("company_id") != company_id or row.get("device_id") != device_id:
            raise PermissionError("cross-tenant or cross-device snapshot")
        if row.get("environment") != "LAB" or row.get("version") != "v0":
            raise PermissionError("LAB v0 scope required")
    if result.get("secret_value_included") is not False:
        return {"status": "HUMAN_REQUIRED", "human_reason": "SECURITY_INCIDENT"}
    if result.get("external_mutation_performed") is not False:
        return {"status": "BLOCKED", "decision": "MUTATION_EVIDENCE_CONFLICT"}
    timestamp = datetime.fromisoformat(command["completed_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("timezone-aware completion required")
    age_seconds = (now - timestamp.astimezone(timezone.utc)).total_seconds()
    flags = ("paired", "extension_connected", "extension_fresh",
             "transport_online", "kill_switch_enabled")
    verified = (
        command.get("state") == "COMPLETED"
        and command.get("semantic_verified") is True
        and result.get("status") == "COMPLETED"
        and result.get("evidence_ref") == "ACCESSBOOT_CAPABILITY_SNAPSHOT"
        and result.get("local_service_version") == "1.4.1"
        and 0 <= age_seconds <= 300
        and all(result.get(name) is True for name in flags)
    )
    profile_count = len(result.get("chrome_profiles") or ()) if verified else None
    return {
        "record_type": "accessboot_capability_assessment",
        "company_id": company_id, "engine_id": "ACCESSBOOT-001",
        "environment": "LAB", "version": "v0",
        "status": "GREEN" if verified else "PARTIAL",
        "profile_count": profile_count,
        "browser_metadata_discovery": bool(verified and
                                           result.get("browser_discovery_status") == "GREEN"),
        "generic_navigation": "NOT_IMPLEMENTED",
        "page_readback": "NOT_IMPLEMENTED",
        "desktop_computer_use": "NOT_IMPLEMENTED",
        "external_mutation_allowed": False,
        "prod_activation_allowed": False,
        "next_block": "ONB_GAP_READ_ONLY_NAVIGATION" if verified else "REFRESH_SNAPSHOT",
        "cost_eur": 0.0,
    }
