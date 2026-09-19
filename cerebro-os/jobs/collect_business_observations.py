from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import asdict
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_ROOT = CEREBRO_OS_ROOT / "discovery"
for candidate in (CEREBRO_OS_ROOT, DISCOVERY_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from discovery.public_web_collector import parse_public_html


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CEREBRO-BusinessObserver/1.0 (+public-read-only)"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        content_type = str(response.headers.get("Content-Type", ""))
        if "text/html" not in content_type.lower():
            raise ValueError("official web source did not return HTML")
        return response.read(2_000_001)


def _quality_issues(snapshot) -> tuple[str, ...]:
    issues: list[str] = []
    if not snapshot.title.strip():
        issues.append("missing_title")
    if not snapshot.h1.strip():
        issues.append("missing_h1")
    if not snapshot.canonical.strip():
        issues.append("missing_canonical")
    if snapshot.title and not 25 <= len(snapshot.title) <= 70:
        issues.append("title_length_review")
    return tuple(issues)


def collect() -> list[Path]:
    config_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_BUSINESS_SOURCES",
        "cerebro-os/config/improvement_business_sources.lab.json",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    state_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT",
        ".cerebro-runtime/observations",
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    state_root.mkdir(parents=True, exist_ok=True)
    sources = json.loads(config_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for source in sources:
        if not source.get("enabled", True):
            continue
        company_id = str(source["company_id"])
        url = str(source.get("official_web_url", "")).strip()
        if not url:
            continue

        output = evidence_root / f"{company_id}.business.json"
        state_path = state_root / f"{company_id}.official-web.json"
        try:
            snapshot = parse_public_html(url, _fetch(url))
            previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
            current = asdict(snapshot)
            issues = _quality_issues(snapshot)
            changed = bool(previous and previous.get("content_hash") != snapshot.content_hash)
            status = "PROPOSAL_READY" if issues or changed else "NO_CHANGE"
            reasons = list(issues)
            if changed:
                reasons.append("official_web_content_changed")
            evidence_ref = f"{snapshot.url}#sha256={snapshot.content_hash}"
            payload = {
                "company_id": company_id,
                "checked": True,
                "source": "OFFICIAL_PUBLIC_WEB",
                "evidence_ref": evidence_ref,
                "status": status,
                "confidence": 0.95,
                "summary": ";".join(reasons) if reasons else "official web checked; no deterministic issue or content delta",
                "facts": {
                    "title": snapshot.title,
                    "h1": snapshot.h1,
                    "canonical": snapshot.canonical,
                    "schema_types": list(snapshot.schema_types),
                    "byte_size": snapshot.byte_size,
                    "content_hash": snapshot.content_hash,
                },
            }
            state_path.write_text(json.dumps(current, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            payload = {
                "company_id": company_id,
                "checked": False,
                "source": "OFFICIAL_PUBLIC_WEB",
                "evidence_ref": f"{url}#collector-error",
                "status": "SOURCE_ERROR",
                "confidence": 0.0,
                "summary": f"public web observation failed: {type(exc).__name__}",
                "facts": {},
            }
        output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(output)

    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
