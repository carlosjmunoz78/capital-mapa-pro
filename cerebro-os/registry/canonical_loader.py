from __future__ import annotations

import json
from pathlib import Path


def load_canonical_registry(path: Path | None = None) -> dict:
    path = path or Path(__file__).with_name("canonical_177.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = data.get("engine_ids", [])
    expected = data.get("engine_count")
    if expected != 177:
        raise ValueError(f"canonical engine_count must be 177, got {expected}")
    if len(ids) != expected:
        raise ValueError(f"registry count mismatch: expected {expected}, got {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate engine_id in canonical registry")
    if not all(isinstance(x, str) and x and x == x.upper() for x in ids):
        raise ValueError("invalid canonical engine_id")
    return data


def canonical_engine_ids(path: Path | None = None) -> tuple[str, ...]:
    return tuple(load_canonical_registry(path)["engine_ids"])
