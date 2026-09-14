from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ("api", "config", "contracts", "observability", "ops")
INCLUDE_FILES = ("manifest.json",)
EXCLUDE_NAMES = {"__pycache__", ".DS_Store"}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDE_NAMES for part in path.parts):
            continue
        result[str(path.relative_to(root))] = _hash_file(path)
    return result


def create_snapshot(source: Path, destination: Path) -> dict[str, str]:
    destination.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE_FILES:
        source_path = source / name
        if source_path.exists():
            shutil.copy2(source_path, destination / name)
    for name in INCLUDE_DIRS:
        source_path = source / name
        if source_path.exists():
            shutil.copytree(source_path, destination / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    hashes = inventory(destination)
    (destination / "snapshot_manifest.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return hashes


def verify_snapshot(snapshot: Path) -> tuple[bool, str]:
    manifest_path = snapshot / "snapshot_manifest.json"
    if not manifest_path.exists():
        return False, "snapshot manifest missing"
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = inventory(snapshot)
    actual.pop("snapshot_manifest.json", None)
    if actual != expected:
        return False, "snapshot hash mismatch"
    return True, "snapshot verified"


def rehearse() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        snapshot = tmp_root / "snapshot"
        restored = tmp_root / "restored"
        expected = create_snapshot(ENGINE_DIR, snapshot)
        ok, reason = verify_snapshot(snapshot)
        if not ok:
            raise RuntimeError(reason)
        shutil.copytree(snapshot, restored)
        (restored / "snapshot_manifest.json").unlink()
        restored_hashes = inventory(restored)
        if restored_hashes != expected:
            raise RuntimeError("restore verification failed")
        return {
            "engine_id": "TAX-001",
            "status": "PASS",
            "scope": "ENGINE_CODE_CONFIG_ONLY",
            "files_verified": len(expected),
            "corpus_artifacts_included": False,
            "prod_touched": False,
        }


if __name__ == "__main__":
    print(json.dumps(rehearse(), sort_keys=True))
