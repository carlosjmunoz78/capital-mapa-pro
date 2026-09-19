from __future__ import annotations

import json
from pathlib import Path

from resilience.company_bundle import write_bundle, verify_bundle


def backup_improvement_state(root: Path, state_root: Path, *, company_id: str, environment: str, version: str) -> Path:
    base = Path(state_root) / company_id / environment / version
    files: dict[str, bytes] = {}
    for name in ("checkpoint.db", "audit.db"):
        path = base / name
        if path.exists():
            files[f"improvement/{name}"] = path.read_bytes()
    if not files:
        raise ValueError("no improvement state to backup")
    return write_bundle(Path(root), company_id, files, version, environment)


def rebuild_improvement_state(root: Path, manifest_path: Path, target_state_root: Path) -> bool:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not verify_bundle(Path(root), manifest):
        return False
    target = Path(target_state_root) / manifest["company_id"] / manifest["environment"] / manifest["version"]
    target.mkdir(parents=True, exist_ok=True)
    bundle_root = Path(root) / manifest["company_id"] / manifest["environment"] / manifest["version"]
    for entry in manifest["files"]:
        if not entry["path"].startswith("improvement/"):
            continue
        (target / Path(entry["path"]).name).write_bytes((bundle_root / entry["path"]).read_bytes())
    return True
