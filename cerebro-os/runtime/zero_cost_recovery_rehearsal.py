from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Mapping


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _smoke(root: Path) -> dict[str, object]:
    files = [path for path in sorted(root.rglob("*")) if path.is_file()]
    json_files = 0
    for path in files:
        data = path.read_bytes()
        if not data:
            raise AssertionError(f"empty restored file: {path.name}")
        if path.suffix.lower() == ".json":
            json.loads(data.decode("utf-8"))
            json_files += 1
    return {"files": len(files), "json_files": json_files, "ok": True}


def rehearse_zero_cost_restore(snapshot_sources: Mapping[str, bytes]) -> dict[str, object]:
    """Rehearse backup -> isolated restore -> integrity -> smoke -> cleanup.

    This is deliberately provider-independent and local/CI-only. It never touches
    Supabase, production data, external credentials, or paid infrastructure.
    """
    if not snapshot_sources:
        raise ValueError("snapshot_sources must not be empty")
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in snapshot_sources):
        raise ValueError("snapshot paths must be relative and traversal-free")

    workspace = Path(tempfile.mkdtemp(prefix="cerebro-recovery-"))
    source = workspace / "source"
    backup = workspace / "backup"
    restored = workspace / "restored"
    cleanup_ok = False
    evidence: dict[str, object] = {}
    try:
        for name, payload in snapshot_sources.items():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bytes(payload))

        source_manifest = _manifest(source)
        shutil.copytree(source, backup)
        backup_manifest = _manifest(backup)
        if backup_manifest != source_manifest:
            raise AssertionError("backup integrity mismatch")

        shutil.copytree(backup, restored)
        restore_manifest = _manifest(restored)
        if restore_manifest != source_manifest:
            raise AssertionError("restore integrity mismatch")

        smoke = _smoke(restored)
        evidence = {
            "mode": "ZERO_COST_LOCAL_CI_ISOLATED",
            "source_files": len(source_manifest),
            "snapshot_manifest": source_manifest,
            "backup_integrity": True,
            "restore_integrity": True,
            "application_smoke": smoke,
            "provider_restore_proven": False,
            "prod_mutated": False,
            "secrets_required": False,
            "additional_cost_eur": 0,
        }
        return evidence
    finally:
        shutil.rmtree(workspace, ignore_errors=False)
        cleanup_ok = not workspace.exists()
        if evidence:
            evidence["cleanup_ok"] = cleanup_ok
