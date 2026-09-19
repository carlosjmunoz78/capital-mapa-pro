from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_ROOT = CEREBRO_OS_ROOT / "discovery"
for candidate in (CEREBRO_OS_ROOT, DISCOVERY_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from discovery.public_web_collector import parse_public_html

_SOCIAL_HOSTS = {
    "facebook.com": "FACEBOOK",
    "instagram.com": "INSTAGRAM",
    "linkedin.com": "LINKEDIN",
    "youtube.com": "YOUTUBE",
    "youtu.be": "YOUTUBE",
    "tiktok.com": "TIKTOK",
}
_LOCAL_SCHEMA_HINTS = {"LocalBusiness", "RealEstateAgent", "FinancialService", "Organization"}


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(str(href).strip())


def _fetch(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CEREBRO-FootprintObserver/1.0 (+public-read-only)"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read(2_000_001), str(response.headers.get("Content-Type", ""))


def _root_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _social_links(base_url: str, html: bytes) -> dict[str, tuple[str, ...]]:
    parser = _LinkParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    result: dict[str, set[str]] = {}
    for raw in parser.links:
        absolute = urllib.parse.urljoin(base_url, raw)
        host = (urllib.parse.urlparse(absolute).hostname or "").lower()
        platform = next((name for domain, name in _SOCIAL_HOSTS.items() if host == domain or host.endswith("." + domain)), None)
        if platform:
            result.setdefault(platform, set()).add(absolute)
    return {k: tuple(sorted(v)) for k, v in sorted(result.items())}


def _probe_text(url: str) -> tuple[bool, str]:
    try:
        body, _ = _fetch(url)
        text = body.decode("utf-8", errors="replace")
        return bool(text.strip()), text[:100_000]
    except Exception:
        return False, ""


def collect() -> list[Path]:
    config_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_BUSINESS_SOURCES",
        "cerebro-os/config/improvement_business_sources.lab.json",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    configs = json.loads(config_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for config in configs:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        urls = config.get("official_web_urls") or []
        if not urls:
            single = str(config.get("official_web_url", "")).strip()
            urls = [single] if single else []
        urls = [str(url).strip() for url in urls if str(url).strip()]
        if not urls:
            continue

        homepage = urls[0]
        root = _root_url(homepage)
        target = evidence_root / f"{company_id}.footprint.json"
        try:
            html, content_type = _fetch(homepage)
            if "html" not in content_type.lower() and content_type:
                raise ValueError("homepage is not HTML")
            snapshot = parse_public_html(homepage, html)
            socials = _social_links(homepage, html)
            robots_ok, robots = _probe_text(urllib.parse.urljoin(root, "robots.txt"))
            sitemap_ok, sitemap = _probe_text(urllib.parse.urljoin(root, "sitemap_index.xml"))
            if not sitemap_ok:
                sitemap_ok, sitemap = _probe_text(urllib.parse.urljoin(root, "sitemap.xml"))
            schema = set(snapshot.schema_types)
            local_schema = bool(schema.intersection(_LOCAL_SCHEMA_HINTS))
            robots_mentions_sitemap = bool(re.search(r"(?im)^\s*sitemap\s*:", robots)) if robots_ok else False

            issues: list[str] = []
            if not robots_ok:
                issues.append("robots_missing_or_unreachable")
            if not sitemap_ok:
                issues.append("sitemap_missing_or_unreachable")
            if not local_schema:
                issues.append("local_or_organization_schema_not_detected")
            if not socials:
                issues.append("social_profile_links_not_detected")
            if robots_ok and sitemap_ok and not robots_mentions_sitemap:
                issues.append("robots_without_sitemap_reference")

            payload = {
                "company_id": company_id,
                "checked": True,
                "source": "PUBLIC_SEO_LOCAL_SOCIAL_FOOTPRINT",
                "evidence_ref": f"{homepage}#sha256={snapshot.content_hash}",
                "status": "PROPOSAL_READY" if issues else "NO_CHANGE",
                "confidence": 0.9,
                "summary": ";".join(issues) if issues else "technical SEO/local/social public footprint checks passed",
                "facts": {
                    "robots_ok": robots_ok,
                    "sitemap_ok": sitemap_ok,
                    "robots_mentions_sitemap": robots_mentions_sitemap,
                    "schema_types": list(snapshot.schema_types),
                    "local_or_org_schema_detected": local_schema,
                    "social_platforms": sorted(socials),
                    "social_links": {k: list(v) for k, v in socials.items()},
                },
            }
        except Exception as exc:
            payload = {
                "company_id": company_id,
                "checked": False,
                "source": "PUBLIC_SEO_LOCAL_SOCIAL_FOOTPRINT",
                "evidence_ref": f"{homepage}#collector-error",
                "status": "SOURCE_ERROR",
                "confidence": 0.0,
                "summary": f"public footprint observation failed: {type(exc).__name__}",
                "facts": {},
            }

        target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
