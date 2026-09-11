from __future__ import annotations

import hashlib
import json
from pathlib import Path

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def build_company_manifest(company_id: str, files: dict[str, bytes], version: str = "0.1.0", environment: str = "LAB") -> dict:
    if not company_id.strip() or not version.strip():
        raise ValueError("company_id and version required")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")
    entries = []
    for relative in sorted(files):
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError("unsafe relative path")
        payload = files[relative]
        entries.append({
            "path": relative,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size": len(payload),
        })
    return {
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "file_count": len(entries),
        "files": entries,
    }


def write_bundle(root: Path, company_id: str, files: dict[str, bytes], version: str = "0.1.0", environment: str = "LAB") -> Path:
    manifest = build_company_manifest(company_id, files, version, environment)
    target = root / company_id / environment / version
    target.mkdir(parents=True, exist_ok=True)
    for relative, payload in files.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    manifest_path = target / "backup_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def verify_bundle(root: Path, manifest: dict) -> bool:
    try:
        company_id = manifest["company_id"]
        environment = manifest["environment"]
        version = manifest["version"]
        files = manifest["files"]
    except (KeyError, TypeError):
        return False
    if not isinstance(company_id, str) or not company_id.strip() or environment not in VALID_ENVIRONMENTS or not isinstance(version, str) or not version.strip():
        return False
    company_root = root / company_id / environment / version
    for entry in files:
        path = company_root / entry["path"]
        if not path.exists():
            return False
        payload = path.read_bytes()
        if len(payload) != entry["size"]:
            return False
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            return False
    return True
