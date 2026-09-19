from __future__ import annotations

import hashlib
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


def _configured_urls(source: dict) -> tuple[str, ...]:
    urls = source.get("official_web_urls")
    if isinstance(urls, list):
        return tuple(str(url).strip() for url in urls if str(url).strip())
    single = str(source.get("official_web_url", "")).strip()
    return (single,) if single else ()


def _state_path(state_root: Path, company_id: str, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return state_root / f"{company_id}.official-web.{digest}.json"


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
        urls = _configured_urls(source)
        if not urls:
            continue

        page_results: list[dict] = []
        for url in urls:
            try:
                snapshot = parse_public_html(url, _fetch(url))
                state_path = _state_path(state_root, company_id, url)
                previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
                current = asdict(snapshot)
                issues = _quality_issues(snapshot)
                changed = bool(previous and previous.get("content_hash") != snapshot.content_hash)
                status = "PROPOSAL_READY" if issues or changed else "NO_CHANGE"
                reasons = list(issues)
                if changed:
                    reasons.append("official_web_content_changed")
                page_results.append({
                    "checked": True,
                    "url": snapshot.url,
                    "evidence_ref": f"{snapshot.url}#sha256={snapshot.content_hash}",
                    "status": status,
                    "confidence": 0.95,
                    "summary": ";".join(reasons) if reasons else "page checked; no deterministic issue or content delta",
                    "facts": {
                        "title": snapshot.title,
                        "h1": snapshot.h1,
                        "canonical": snapshot.canonical,
                        "schema_types": list(snapshot.schema_types),
                        "byte_size": snapshot.byte_size,
                        "content_hash": snapshot.content_hash,
                    },
                })
                state_path.write_text(json.dumps(current, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            except Exception as exc:
                page_results.append({
                    "checked": False,
                    "url": url,
                    "evidence_ref": f"{url}#collector-error",
                    "status": "SOURCE_ERROR",
                    "confidence": 0.0,
                    "summary": f"public web observation failed: {type(exc).__name__}",
                    "facts": {},
                })

        checked = [item for item in page_results if item["checked"]]
        if checked:
            proposals = [item for item in checked if item["status"] == "PROPOSAL_READY"]
            chosen = proposals[0] if proposals else checked[0]
            status = "PROPOSAL_READY" if proposals else "NO_CHANGE"
            confidence = min(float(item["confidence"]) for item in checked)
        else:
            chosen = page_results[0]
            status = "SOURCE_ERROR"
            confidence = 0.0

        output = evidence_root / f"{company_id}.business.json"
        payload = {
            "company_id": company_id,
            "checked": bool(checked),
            "source": "OFFICIAL_PUBLIC_WEB_PORTFOLIO",
            "evidence_ref": chosen["evidence_ref"],
            "status": status,
            "confidence": confidence,
            "summary": " | ".join(f'{item["url"]}:{item["status"]}:{item["summary"]}' for item in page_results),
            "facts": {
                "pages_checked": len(checked),
                "pages_configured": len(page_results),
                "proposal_pages": sum(1 for item in page_results if item["status"] == "PROPOSAL_READY"),
                "source_errors": sum(1 for item in page_results if item["status"] == "SOURCE_ERROR"),
                "pages": page_results,
            },
        }
        output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(output)

    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
