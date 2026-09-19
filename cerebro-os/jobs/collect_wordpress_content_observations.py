from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


def _fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CEREBRO-ContentObserver/1.0 (+public-read-only)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def _endpoint(base: str, kind: str) -> str:
    query = urllib.parse.urlencode({
        "per_page": 5,
        "orderby": "modified",
        "order": "desc",
        "_fields": "id,modified,link,slug,status",
    })
    return f"{base.rstrip('/')}/{kind}?{query}"


def _normalize(items: object) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("WordPress REST response must be a list")
    result: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("WordPress REST item must be an object")
        result.append({
            "id": int(item.get("id", 0)),
            "modified": str(item.get("modified", "")),
            "link": str(item.get("link", "")),
            "slug": str(item.get("slug", "")),
            "status": str(item.get("status", "")),
        })
    return result


def _latest_modified(items: list[dict]) -> str:
    values = [str(item.get("modified", "")).strip() for item in items if str(item.get("modified", "")).strip()]
    return max(values) if values else ""


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
    configs = json.loads(config_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for config in configs:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        base = str(config.get("wordpress_rest_base", "")).strip()
        if not base:
            continue

        target = evidence_root / f"{company_id}.content.json"
        state_path = state_root / f"{company_id}.wordpress-content.json"
        try:
            posts = _normalize(_fetch_json(_endpoint(base, "posts")))
            pages = _normalize(_fetch_json(_endpoint(base, "pages")))
            current = {
                "posts": posts,
                "pages": pages,
                "latest_post_modified": _latest_modified(posts),
                "latest_page_modified": _latest_modified(pages),
            }
            previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
            changed = bool(previous and previous != current)
            zero_content = not posts and not pages
            status = "PROPOSAL_READY" if zero_content else "NO_CHANGE"
            summary_parts = [
                f"posts_observed={len(posts)}",
                f"pages_observed={len(pages)}",
                f"content_delta={'yes' if changed else 'no'}",
            ]
            if zero_content:
                summary_parts.append("public_content_empty")
            payload = {
                "company_id": company_id,
                "checked": True,
                "source": "WORDPRESS_PUBLIC_REST",
                "evidence_ref": f"{base}#posts-pages",
                "status": status,
                "confidence": 0.95,
                "summary": ";".join(summary_parts),
                "facts": current,
            }
            state_path.write_text(json.dumps(current, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            payload = {
                "company_id": company_id,
                "checked": False,
                "source": "WORDPRESS_PUBLIC_REST",
                "evidence_ref": f"{base}#collector-error",
                "status": "SOURCE_ERROR",
                "confidence": 0.0,
                "summary": f"WordPress content observation failed: {type(exc).__name__}",
                "facts": {},
            }
        target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
