from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_source_directory(source_dir: Path, lock_path: Path) -> dict[str, str]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    results: dict[str, str] = {}
    for item in lock["sources"]:
        domain = item["domain"]
        if item["status"] == "MISSING_ARTIFACT":
            results[domain] = "MISSING_ARTIFACT"
            continue
        path = source_dir / item["file"]
        if not path.exists():
            results[domain] = "MISSING_ARTIFACT"
            continue
        if path.stat().st_size != item["bytes"]:
            results[domain] = "SIZE_MISMATCH"
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            results[domain] = "HASH_MISMATCH"
            continue
        results[domain] = "VERIFIED"
    return results


def all_bound_sources_verified(results: dict[str, str]) -> bool:
    return all(status in {"VERIFIED", "MISSING_ARTIFACT"} for status in results.values()) and sum(
        status == "VERIFIED" for status in results.values()
    ) == 11
