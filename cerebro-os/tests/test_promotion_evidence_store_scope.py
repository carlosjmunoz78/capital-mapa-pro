from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


store_mod = load("promotion_store", "registry/evidence_store.py")
promo = load("promotion_evidence_scope", "registry/promotion_evidence.py")


def test_exact_scope_requires_all_promotion_kinds():
    with tempfile.TemporaryDirectory() as td:
        store = store_mod.EvidenceStore(Path(td) / "evidence.sqlite")
        for kind in promo.REQUIRED_KINDS:
            store.append(company_id="fenix", engine_id="FACT-001", version="1", environment="PROD", kind=kind, reference=f"proof:{kind}")
        result = promo.collect_promotion_evidence(evidence_store=store, company_id="fenix", engine_id="FACT-001", version="1", environment="PROD")
        assert result["ready"] is True
        assert result["missing"] == ()
        store.close()


def test_other_company_version_and_environment_cannot_satisfy_gate():
    with tempfile.TemporaryDirectory() as td:
        store = store_mod.EvidenceStore(Path(td) / "evidence.sqlite")
        store.append(company_id="other", engine_id="FACT-001", version="1", environment="PROD", kind="tests", reference="wrong-company")
        store.append(company_id="fenix", engine_id="FACT-001", version="2", environment="PROD", kind="tests", reference="wrong-version")
        store.append(company_id="fenix", engine_id="FACT-001", version="1", environment="PREPROD", kind="tests", reference="wrong-env")
        result = promo.collect_promotion_evidence(evidence_store=store, company_id="fenix", engine_id="FACT-001", version="1", environment="PROD")
        assert result["ready"] is False
        assert "tests" in result["missing"]
        store.close()


def test_unknown_evidence_kind_does_not_fake_gate():
    with tempfile.TemporaryDirectory() as td:
        store = store_mod.EvidenceStore(Path(td) / "evidence.sqlite")
        store.append(company_id="fenix", engine_id="FACT-001", version="1", environment="PROD", kind="generic_green", reference="not-a-gate")
        result = promo.collect_promotion_evidence(evidence_store=store, company_id="fenix", engine_id="FACT-001", version="1", environment="PROD")
        assert result["ready"] is False
        assert len(result["missing"]) == len(promo.REQUIRED_KINDS)
        assert result["ignored_evidence_ids"]
        store.close()
