"""FACT-001 batch scaffold preflight and local rollback.

No network enrollment is permitted during this batch operation: after a network
send an in-process rollback could not guarantee the remote event is cancelled.
All actions happen in the caller-provided isolated LAB repository.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import shutil
import stat


class EngineSpec:
    def __init__(self, engine_id: str, name: str, company_scope: str = "multi"):
        self.engine_id = engine_id
        self.name = name
        self.company_scope = company_scope


def _load_factory():
    path = Path(__file__).with_name("factory.py")
    spec = importlib.util.spec_from_file_location("cerebro_factory_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("factory module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_ids(ids, factory):
    if not isinstance(ids, (list, tuple)):
        raise ValueError("engine_ids must be an ordered list or tuple")
    canonical = [factory.validate_engine_id(i) for i in ids]
    if len(canonical) != len(set(canonical)):
        raise ValueError("duplicate engine_id after canonicalization")
    return canonical


class MassScaffoldPlan:
    def __init__(self, engine_specs):
        self.engine_specs = list(engine_specs)

    def validate(self):
        _canonical_ids([s.engine_id for s in self.engine_specs], _load_factory())
        return True

    def output_paths(self, root: str = "generated-engines"):
        canonical = _canonical_ids([s.engine_id for s in self.engine_specs], _load_factory())
        return [str(Path(root) / engine_id) for engine_id in canonical]


def _remote_enrollment_enabled(env):
    return bool(env.get("CEREBRO_COMPANY_ID") and all(env.get(k) for k in (
        "CEREBRO_FACT_ENROLL_EVENT_KEY", "CEREBRO_CLOUDFLARE_API_TOKEN",
        "CEREBRO_CLOUDFLARE_ACCOUNT_ID", "CEREBRO_FACT_ENROLL_QUEUE_ID",
    )))


def generate_all(root: Path, engine_ids: list[str] | tuple[str, ...]) -> list[Path]:
    """Create a validated local batch; roll back only directories created in it.

    Refuses concurrent batches (exclusive lock), existing engine IDs, invalid IDs,
    symlinked roots and remote queue dispatch. This does not offer cross-service
    transaction semantics, and does not mutate existing engine directories.
    """
    factory = _load_factory()
    ids = _canonical_ids(engine_ids, factory)
    if _remote_enrollment_enabled(os.environ):
        raise ValueError("BATCH_REMOTE_ENROLLMENT_REQUIRES_SEPARATE_COMMIT_ACK")
    root = Path(root).absolute()
    if root.is_symlink():
        raise ValueError("ROOT_SYMLINK_DENIED")
    engines = root / "engines"
    if engines.is_symlink():
        raise ValueError("ENGINES_SYMLINK_DENIED")
    # Non-destructive preflight; no existing destination is modified or removed.
    for engine_id in ids:
        target = engines / engine_id
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"engine already exists: {engine_id}")
    if not ids:
        return []
    engines.mkdir(parents=True, exist_ok=True)
    lock = engines / ".fact001-mass-scaffold.lock"
    fd = None
    owned_inode = None
    try:
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise RuntimeError("MASS_SCAFFOLD_ALREADY_RUNNING") from exc
        lockstat = os.fstat(fd)
        owned_inode = (lockstat.st_dev, lockstat.st_ino)
        os.write(fd, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(fd)
        fd = None
        created = []
        try:
            # Repeat preflight under our own batch lock.
            for engine_id in ids:
                target = engines / engine_id
                if target.exists() or target.is_symlink():
                    raise FileExistsError(f"engine already exists: {engine_id}")
            for engine_id in ids:
                target = engines / engine_id
                if target.exists() or target.is_symlink():
                    raise FileExistsError(f"engine already exists: {engine_id}")
                # Record expected destination *before* calling the hook, so a
                # mid-scaffold failure can also be cleaned up.
                created.append(target)
                actual = factory.scaffold(root, engine_id, engine_id)
                if Path(actual).absolute() != target:
                    raise RuntimeError("FACTORY_RETURNED_UNEXPECTED_TARGET")
            return created
        except BaseException as error:
            failed = []
            for target in reversed(created):
                if target.is_symlink():
                    failed.append(target.name + ":symlink")
                    continue
                if target.is_dir():
                    try:
                        shutil.rmtree(target)
                    except OSError:
                        failed.append(target.name)
                elif target.exists():
                    failed.append(target.name + ":unexpected-type")
            if failed:
                raise RuntimeError("BATCH_ROLLBACK_INCOMPLETE:" + ",".join(failed)) from error
            raise
    finally:
        if fd is not None:
            os.close(fd)
        # Never delete a lock owned or replaced by another process.
        if owned_inode is not None:
            try:
                now = lock.lstat()
                if stat.S_ISREG(now.st_mode) and (now.st_dev, now.st_ino) == owned_inode:
                    lock.unlink()
            except FileNotFoundError:
                pass