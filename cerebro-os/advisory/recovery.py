from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256

from .case_context import CaseSnapshot, CaseStore


@dataclass(frozen=True)
class AdvisoryBackupBundle:
    schema_version: str
    created_from_version: str
    snapshots: tuple[CaseSnapshot, ...]
    rollback_ref: str

    def validate(self) -> None:
        if not self.schema_version.strip() or not self.created_from_version.strip():
            raise ValueError("backup schema/version required")
        if not self.rollback_ref.strip():
            raise ValueError("rollback_ref required")
        for snapshot in self.snapshots:
            snapshot.validate()

    def canonical_payload(self) -> str:
        self.validate()
        payload = {
            "schema_version": self.schema_version,
            "created_from_version": self.created_from_version,
            "rollback_ref": self.rollback_ref,
            "snapshots": [asdict(snapshot) for snapshot in self.snapshots],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return sha256(self.canonical_payload().encode("utf-8")).hexdigest()


def create_backup(
    snapshots: tuple[CaseSnapshot, ...],
    *,
    version: str,
    rollback_ref: str,
) -> AdvisoryBackupBundle:
    bundle = AdvisoryBackupBundle(
        schema_version="1.0.0",
        created_from_version=version,
        snapshots=snapshots,
        rollback_ref=rollback_ref,
    )
    bundle.validate()
    bundle.digest()
    return bundle


def rebuild_case_store(bundle: AdvisoryBackupBundle) -> CaseStore:
    bundle.validate()
    store = CaseStore()
    for snapshot in bundle.snapshots:
        store.save(snapshot)
    return store


def rollback_target(bundle: AdvisoryBackupBundle) -> str:
    bundle.validate()
    return bundle.rollback_ref
