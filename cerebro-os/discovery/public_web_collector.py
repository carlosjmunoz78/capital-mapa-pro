from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import ipaddress
import json
from urllib.parse import urljoin, urlparse

from competitor_observation import CompetitorObservation

MAX_HTML_BYTES = 2_000_000


def validate_public_url(url: str) -> str:
    value = url.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("public web collector requires http/https URL with hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not allowed")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("localhost is not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return value
    if not ip.is_global:
        raise ValueError("non-global IP address is not allowed")
    return value


def normalize_text(value: str) -> str:
    return " ".join(value.split())


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture: str | None = None
        self._buf: list[str] = []
        self.title = ""
        self.h1 = ""
        self.canonical = ""
        self.schema_types: set[str] = set()
        self._json_ld_depth = 0
        self._json_ld_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): (v or "") for k, v in attrs}
        lowered = tag.lower()
        if lowered == "title" and not self.title:
            self._capture = "title"
            self._buf = []
        elif lowered == "h1" and not self.h1:
            self._capture = "h1"
            self._buf = []
        elif lowered == "link" and not self.canonical:
            rel = {part.lower() for part in attrs_map.get("rel", "").split()}
            if "canonical" in rel:
                self.canonical = attrs_map.get("href", "").strip()
        elif lowered == "script" and attrs_map.get("type", "").lower() == "application/ld+json":
            self._json_ld_depth = 1
            self._json_ld_buf = []

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._capture == lowered:
            text = normalize_text("".join(self._buf))
            if lowered == "title":
                self.title = text
            elif lowered == "h1":
                self.h1 = text
            self._capture = None
            self._buf = []
        if lowered == "script" and self._json_ld_depth:
            raw = "".join(self._json_ld_buf).strip()
            self._json_ld_depth = 0
            self._json_ld_buf = []
            if raw:
                self._consume_json_ld(raw)

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)
        if self._json_ld_depth:
            self._json_ld_buf.append(data)

    def _consume_json_ld(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return

        def walk(node: object) -> None:
            if isinstance(node, dict):
                kind = node.get("@type")
                if isinstance(kind, str) and kind.strip():
                    self.schema_types.add(kind.strip())
                elif isinstance(kind, list):
                    self.schema_types.update(str(x).strip() for x in kind if str(x).strip())
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)


@dataclass(frozen=True)
class PublicWebSnapshot:
    url: str
    title: str
    h1: str
    canonical: str
    schema_types: tuple[str, ...]
    content_hash: str
    byte_size: int


def parse_public_html(url: str, html: bytes | str) -> PublicWebSnapshot:
    safe_url = validate_public_url(url)
    raw = html.encode("utf-8") if isinstance(html, str) else bytes(html)
    if not raw:
        raise ValueError("empty HTML response")
    if len(raw) > MAX_HTML_BYTES:
        raise ValueError("HTML response exceeds collector byte limit")
    text = raw.decode("utf-8", errors="replace")
    parser = _PageParser()
    parser.feed(text)
    canonical = urljoin(safe_url, parser.canonical) if parser.canonical else safe_url
    validate_public_url(canonical)
    return PublicWebSnapshot(
        url=safe_url,
        title=parser.title,
        h1=parser.h1,
        canonical=canonical,
        schema_types=tuple(sorted(parser.schema_types)),
        content_hash=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
    )


def snapshot_observations(
    snapshot: PublicWebSnapshot,
    *,
    company_id: str,
    competitor_id: str,
    environment: str = "LAB",
    version: str = "1.0.0",
    engine_id: str = "COMPET-001",
    evidence_ref: str,
    observed_at: str | None = None,
    confidence: float = 0.95,
    cost_units: float = 0.0,
) -> tuple[CompetitorObservation, ...]:
    observed = observed_at or datetime.now(timezone.utc).isoformat()
    facts = [
        ("page_fingerprint", snapshot.content_hash),
        ("title", snapshot.title),
        ("h1", snapshot.h1),
        ("canonical", snapshot.canonical),
        ("schema_types", ",".join(snapshot.schema_types)),
    ]
    result: list[CompetitorObservation] = []
    for metric, value in facts:
        if not value:
            continue
        fact_hash = hashlib.sha256(f"{metric}\0{value}".encode("utf-8")).hexdigest()
        item = CompetitorObservation(
            company_id=company_id,
            competitor_id=competitor_id,
            engine_id=engine_id,
            environment=environment,
            version=version,
            source=snapshot.url,
            source_type="WEB",
            observed_at=observed,
            url_or_external_id=snapshot.url,
            metric_or_fact=metric,
            value=value,
            content_hash=fact_hash,
            evidence_ref=evidence_ref,
            confidence=confidence,
            cost_units=cost_units if metric == "page_fingerprint" else 0.0,
        )
        item.validate()
        result.append(item)
    return tuple(result)
