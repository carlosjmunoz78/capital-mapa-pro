from __future__ import annotations

import hashlib
import json
from pathlib import Path


def build_company_manifest(company_id: str, files: dict[str, bytes], version: str = "0.1.0") -> dict:
    if not company_id:
        raise ValueError("company_id required")
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
        "version": version,
        "file_count": len(entries),
        "files": entries,
    }


def write_bundle(root: Path, company_id: str, files: dict[str, bytes], version: str = "0.1.0") -> Path:
    target = root / company_id
    target.mkdir(parents=True, exist_ok=True)
    for relative, payload in files.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    manifest = build_company_manifest(company_id, files, version)
    manifest_path = target / "backup_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def verify_bundle(root: Path, manifest: dict) -> bool:
    company_root = root / manifest["company_id"]
    for entry in manifest["files"]:
        path = company_root / entry["path"]
        if not path.exists():
            return False
        payload = path.read_bytes()
        if len(payload) != entry["size"]:
            return False
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            return False
    return True
