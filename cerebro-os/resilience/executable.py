from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_file(source: Path, backup: Path) -> str:
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, backup)
    return sha256(backup)


def restore_file(backup: Path, target: Path, expected_sha256: str) -> None:
    if sha256(backup) != expected_sha256:
        raise ValueError("backup checksum mismatch")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    if sha256(target) != expected_sha256:
        raise ValueError("restore verification failed")


def rebuild_directory(target: Path, required_dirs: tuple[str, ...]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for relative in required_dirs:
        (target / relative).mkdir(parents=True, exist_ok=True)
