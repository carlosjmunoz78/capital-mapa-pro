from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, TextIO

REQUIRED_SCOPE = ("company_id", "engine_id", "environment", "version")
ALLOWED_KINDS = {"log", "metric", "incident"}
FORBIDDEN_KEYS = {
    "password", "passwd", "secret", "secret_value", "token", "access_token",
    "refresh_token", "api_key", "apikey", "authorization", "cookie",
    "service_role_key", "private_key",
}


def _contains_secret(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower().strip()
            child_path = f"{path}.{key}" if path else str(key)
            if key_text in FORBIDDEN_KEYS or any(marker in key_text for marker in ("password", "secret", "token", "api_key", "private_key")):
                hits.append(child_path)
            hits.extend(_contains_secret(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_contains_secret(child, f"{path}[{index}]"))
    return hits


def validate_event(event: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_SCOPE if not str(event.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing scope fields: {','.join(missing)}")
    if event.get("kind") not in ALLOWED_KINDS:
        raise ValueError("kind must be log, metric, or incident")
    secret_paths = _contains_secret(event)
    if secret_paths:
        raise ValueError(f"secret-like fields forbidden: {','.join(secret_paths)}")


class JsonlObservabilitySink:
    """Zero-cost append-only auxiliary sink for non-secret observability envelopes.

    It is intentionally filesystem-based so LAB/runner/local deployments do not
    consume Supabase transactional capacity. Production wiring remains a separate gate.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> None:
        validate_event(event)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def replay(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"corrupt JSONL line {number}") from exc
                validate_event(event)
                events.append(event)
        return events

    def scoped(self, *, company_id: str, engine_id: str, environment: str, version: str) -> list[dict[str, Any]]:
        return [
            event for event in self.replay()
            if event["company_id"] == company_id
            and event["engine_id"] == engine_id
            and event["environment"] == environment
            and event["version"] == version
        ]


class StructuredStdoutObservabilitySink:
    """Emit validated JSON envelopes to stdout for managed-runtime collection.

    The sink owns no external credential, creates no network connection, and performs
    no direct write to App/CRM/Supabase. In managed runtimes such as Cloud Run, stdout
    can be collected by the platform without adding a second application datastore.
    Persistence/retention in a target environment must still be evidenced separately.
    """

    def __init__(self, stream: TextIO | None = None):
        self.stream = stream if stream is not None else sys.stdout

    def emit(self, event: dict[str, Any]) -> str:
        validate_event(event)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.stream.write(line + "\n")
        self.stream.flush()
        return line


def coverage(events: Iterable[dict[str, Any]]) -> dict[str, bool]:
    kinds = {event.get("kind") for event in events}
    return {kind: kind in kinds for kind in sorted(ALLOWED_KINDS)}
