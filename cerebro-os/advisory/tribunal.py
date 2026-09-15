from __future__ import annotations

import json
from pathlib import Path


def adjudicate(readiness_path: Path, bootstrap_report_path: Path) -> dict:
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    report = json.loads(bootstrap_report_path.read_text(encoding="utf-8"))

    steps = {row["id"]: row for row in readiness["steps"]}
    missing_domains = [row["domain"] for row in report["domains"] if row["verification"] == "MISSING_ARTIFACT"]

    architecture_green = all(steps[i]["status"] == "GREEN" for i in range(1, 11))
    all_sources_present = not missing_domains
    ready_for_12_domain_tribunal = architecture_green and all_sources_present

    if ready_for_12_domain_tribunal:
        verdict = "READY_FOR_KNOWLEDGE_VALIDATION"
        blocker = None
    else:
        verdict = "BLOCKED"
        blocker = "MISSING_ARTIFACT" if missing_domains else "UNMET_GATE"

    return {
        "component_id": "PROFESSIONAL_ADVISORY",
        "environment": "LAB",
        "architecture_green": architecture_green,
        "source_integrity_verified_domains": report["summary"]["physically_verified"],
        "missing_domains": missing_domains,
        "ready_for_12_domain_tribunal": ready_for_12_domain_tribunal,
        "verdict": verdict,
        "blocker": blocker,
        "knowledge_green": False,
        "capability_green": False,
        "autonomy_green": False,
        "prod_enabled": False,
    }
