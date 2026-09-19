import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from observability.improvement_audit_store import ImprovementAuditRecord, ImprovementAuditStore


class ImprovementAuditTests(unittest.TestCase):
    def record(self, stage="OBSERVE", status="GREEN", cost=0.0):
        return ImprovementAuditRecord(
            company_id="aion", engine_id="SUP-IMPROVEMENT", environment="LAB", version="1.0.0",
            cycle_id="cycle-001", stage=stage, status=status, evidence_ref=f"e://{stage}",
            old_ref="old://v1", new_ref="new://v2", rollback_ref="rollback://v1", cost_eur=cost,
            occurred_at="2026-09-19T12:00:00+00:00",
        )

    def test_append_and_verify_chain(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementAuditStore(Path(td) / "audit.db")
            store.append(self.record())
            store.append(self.record("TEST"))
            self.assertTrue(store.verify_chain(company_id="aion", environment="LAB"))
            self.assertEqual(len(store.cycle_records(company_id="aion", environment="LAB", cycle_id="cycle-001")), 2)
            store.close()

    def test_tampering_detected(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementAuditStore(Path(td) / "audit.db")
            store.append(self.record())
            store.conn.execute("UPDATE improvement_audit SET payload_json='{}'")
            store.conn.commit()
            self.assertFalse(store.verify_chain(company_id="aion", environment="LAB"))
            store.close()

    def test_company_environment_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementAuditStore(Path(td) / "audit.db")
            store.append(self.record())
            self.assertEqual(store.cycle_records(company_id="fenix", environment="LAB", cycle_id="cycle-001"), [])
            self.assertEqual(store.cycle_records(company_id="aion", environment="PREPROD", cycle_id="cycle-001"), [])
            store.close()

    def test_negative_cost_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementAuditStore(Path(td) / "audit.db")
            with self.assertRaises(ValueError):
                store.append(self.record(cost=-0.01))
            store.close()

    def test_missing_evidence_fails_closed(self):
        r = self.record()
        bad = ImprovementAuditRecord(**{**r.__dict__, "evidence_ref": ""})
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementAuditStore(Path(td) / "audit.db")
            with self.assertRaises(ValueError):
                store.append(bad)
            store.close()

if __name__ == "__main__":
    unittest.main()
