from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IntegrationHealthSummary:
    crm_status: str
    gsc_status: str
    social_status: str
    youtube_status: str
    overall_status: str
    blockers: tuple[str, ...]


def assess_live_snapshot(path: Path) -> IntegrationHealthSummary:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("mode") != "READ_ONLY_LIVE_AUDIT":
        raise ValueError("live integration evidence must be read-only")

    supabase = payload.get("supabase") or {}
    crm_status = "GREEN" if supabase.get("project_status") == "ACTIVE_HEALTHY" else "BLOCKED"

    make = payload.get("make") or {}
    gsc = make.get("gsc") or {}
    gsc_status = "GREEN" if (
        gsc.get("status") == "active"
        and gsc.get("incomplete_executions") == 0
        and all(x == "ok" for x in gsc.get("connection_statuses", []))
        and bool(gsc.get("latest_success_started_at"))
    ) else "BLOCKED"

    social_items = [make.get("facebook_health") or {}, make.get("instagram_health") or {}, make.get("linkedin_health") or {}]
    social_status = "GREEN" if all(
        item.get("latest_probe_status") == "success"
        and item.get("incomplete_executions") == 0
        and all(x == "ok" for x in item.get("connection_statuses", []))
        for item in social_items
    ) else "BLOCKED"

    youtube = make.get("youtube_health") or {}
    youtube_status = "BLOCKED" if youtube.get("status") == "error" else "GREEN"

    blockers = []
    if crm_status != "GREEN":
        blockers.append("CRM_LIVE_HEALTH")
    if gsc_status != "GREEN":
        blockers.append("GSC_CAPTURE_HEALTH")
    if social_status != "GREEN":
        blockers.append("SOCIAL_HEALTH")
    if youtube_status != "GREEN":
        blockers.append("YOUTUBE_CONNECTION_VALIDATION")

    # YouTube is isolated from the already-green CRM/GSC/social observers.
    # Its failure is visible but does not falsify the health of unrelated sources.
    overall = "PARTIAL" if blockers else "GREEN"
    return IntegrationHealthSummary(
        crm_status=crm_status,
        gsc_status=gsc_status,
        social_status=social_status,
        youtube_status=youtube_status,
        overall_status=overall,
        blockers=tuple(blockers),
    )
