from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "multicompany" / "backup_gate.py"

spec = importlib.util.spec_from_file_location("backup_gate_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def all_refs() -> dict[str, str]:
    return {name: f"evidence:{name}" for name in mod.CHECKS}


def test_true_booleans_without_evidence_are_not_ready():
    result = mod.backup_gate(
        company_id="fenix",
        backup_verified=True,
        restore_verified=True,
        rebuild_verified=True,
        rollback_verified=True,
    )
    assert result["ready"] is False
    assert set(result["missing_evidence"]) == set(mod.CHECKS)


def test_missing_restore_remains_explicit_even_with_other_evidence():
    refs = all_refs()
    result = mod.backup_gate(
        company_id="fenix",
        backup_verified=True,
        restore_verified=False,
        rebuild_verified=True,
        rollback_verified=True,
        evidence_refs=refs,
    )
    assert result["ready"] is False
    assert result["missing"] == ("restore_verified",)


def test_complete_recovery_proof_is_ready():
    result = mod.backup_gate(
        company_id="fenix",
        backup_verified=True,
        restore_verified=True,
        rebuild_verified=True,
        rollback_verified=True,
        evidence_refs=all_refs(),
    )
    assert result["ready"] is True
    assert result["missing"] == ()
    assert result["missing_evidence"] == ()
