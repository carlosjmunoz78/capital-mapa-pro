import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"registry"/"instances"/"SUP-001_FACT001-P5_CP88.lab.json"
class CP88PhysicalInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads(FILE.read_text(encoding="utf-8"))
    def test_exact_canonical_scope_and_evidence(self):
        d=self.record
        self.assertEqual(d["record_type"],"PHYSICAL_LAB_ADMIN_REGISTRATION")
        self.assertEqual(d["instance_key"],"fenix-capital:SUP-001:LAB:FACT001-P5")
        self.assertEqual(d["engine_id"],"SUP-001")
        self.assertEqual(d["environment"],"LAB")
        self.assertEqual(d["lifecycle_state"],"LAB_SCOPED_VERIFIED")
        self.assertEqual(d["source_snapshot_id"],"GOV-001:FACT-001:P5:LAB:20261123")
        self.assertEqual(d["source_sha256"],"53dd8838848cfa0910e94b16cf7794037e25405df07219a6cc279eb2c58fd713")
        self.assertTrue(d["notion_registry_mirror_not_source_of_truth"])
    def test_no_prod_no_new_grants_no_media_dispatch(self):
        d=self.record
        for prop in ("production_authorized","new_execution_grants","media_dispatch_enabled"):
            self.assertEqual(d[prop],0)
        self.assertEqual(d["cost_additional_ceiling_eur"],0)
        self.assertEqual(d["enrollment_status"],"HOLD_FACTORY_IAM_SCOPE")
        m=d["manifest"]
        self.assertEqual(m["canonical_engine_id"],"SUP-001")
        self.assertEqual(m["registration_method"],"ADMIN_READONLY_EVIDENCE_SEED")
        self.assertFalse(m["policy"]["production_authorized"])
        self.assertFalse(m["evaluation"]["promotion_gate_passed"])
        self.assertFalse(m["rebuild"]["completed"])
if __name__=="__main__":
    unittest.main()
