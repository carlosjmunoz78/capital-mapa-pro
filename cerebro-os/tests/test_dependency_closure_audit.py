from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "governance" / "dependency_closure.py"

spec = importlib.util.spec_from_file_location("dependency_closure_audit", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_partial_dependency_map_is_not_valid():
    graph = mod.DependencyClosure(("A", "B", "C"))
    graph.add("A", ("B",))
    audit = graph.audit()
    assert audit["valid"] is False
    assert audit["unmapped_canonical"] == ("B", "C")
    assert audit["dependency_only_nodes"] == ("B",)


def test_complete_dependency_map_is_valid():
    graph = mod.DependencyClosure(("A", "B", "C"))
    graph.add("B", ())
    graph.add("A", ("B",))
    graph.add("C", ("A",))
    audit = graph.audit()
    assert audit["valid"] is True
    assert audit["unmapped_canonical"] == ()
    assert audit["dependency_only_nodes"] == ()


def test_duplicate_canonical_ids_fail_closed():
    try:
        mod.DependencyClosure(("A", "A"))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate canonical IDs must fail")
