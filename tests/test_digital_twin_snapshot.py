import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.build_digital_twin_snapshot import build_snapshot,run

class DigitalTwinTests(unittest.TestCase):
    def test_company_scoped_snapshot_is_non_prod_and_hashed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; inv.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{"company_id":"fenix","knowledge_id":"k1"}]),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            try: snap=build_snapshot("fenix","LAB","1.0.0")
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(snap["engine_id"],"TWIN-001")
            self.assertEqual(snap["source_count"],1)
            self.assertTrue(snap["snapshot_id"].startswith("twin-"))
            self.assertTrue(snap["synthetic_overlay_only"])
            self.assertFalse(snap["writes_to_prod"])
            self.assertFalse(snap["external_mutation_allowed"])
            self.assertFalse(snap["live_traffic_exposed"])

    def test_cross_company_source_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; inv.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{"company_id":"aion","knowledge_id":"k"}]),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            try:
                with self.assertRaisesRegex(ValueError,"cross-company"): build_snapshot("fenix","LAB","1")
            finally: os.environ.clear(); os.environ.update(old)

    def test_prod_snapshot_target_denied(self):
        with self.assertRaisesRegex(ValueError,"must not target PROD"):
            build_snapshot("fenix","PROD","1")

if __name__=="__main__": unittest.main()
