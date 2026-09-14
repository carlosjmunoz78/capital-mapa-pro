from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Aud001TaxPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module("tax_audit", ROOT / "engines" / "TAX-001" / "observability" / "audit.py")
        cls.sink_mod = load_module("aud_sink", ROOT / "engines" / "AUD-001" / "api" / "audit_sink.py")

    def test_tax_event_persists_partitioned_and_append_only(self):
        payload = {"request_id": "req-1", "company_id": "co-1", "operation": "CALCULATE"}
        result = {"status": "RULE_EXECUTED", "human_required": None, "evidence_refs": ["BOE:demo"], "cost_eur": 0.0}
        event = self.audit.build_audit_event(payload, result, duration_ms=7)
        with tempfile.TemporaryDirectory() as tmp:
            sink = self.sink_mod.JsonlAuditSink(tmp)
            first = self.audit.persist_audit_event(event, sink)
            second = self.audit.persist_audit_event(event, sink)
            path = Path(first["path"])
            self.assertEqual(path, Path(second["path"]))
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            record = json.loads(lines[0])
            self.assertEqual(record["company_id"], "co-1")
            self.assertEqual(record["engine_id"], "TAX-001")
            self.assertEqual(record["persistence_owner"], "AUD-001")
            self.assertEqual(record["persistence_status"], "PERSISTED")

    def test_missing_company_fails_closed(self):
        event = {
            "event_type": "tax.decision_support.audited",
            "occurred_at": "2026-09-15T00:00:00+00:00",
            "request_id": "req-2",
            "company_id": "",
            "engine_id": "TAX-001",
            "version": "0.1.0",
            "environment": "LAB",
            "result": "RULE_EXECUTED",
            "persistence_owner": "AUD-001",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                self.sink_mod.JsonlAuditSink(tmp).persist(event)


if __name__ == "__main__":
    unittest.main()
