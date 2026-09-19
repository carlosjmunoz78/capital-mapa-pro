import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.run_company_backup_restore_rehearsal import build_backup,restore_rehearsal
from jobs.rebuild_company_derived_state import rebuild_company
from jobs.assess_business_continuity import assess

class BackupRebuildContinuityTests(unittest.TestCase):
    def test_backup_and_restore_rehearsal_verify_hashes_without_live_restore(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=root/"runtime"; backup=root/"backup"
            (runtime/"knowledge-inventory").mkdir(parents=True)
            (runtime/"knowledge-inventory"/"aion.json").write_text(json.dumps([{"company_id":"aion","knowledge_id":"k"}]),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_RUNTIME_ROOT"]=str(runtime); os.environ["CEREBRO_BACKUP_ROOT"]=str(backup)
            try:
                result=build_backup("aion")
                rehearsal=restore_rehearsal("aion")
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(result["file_count"],1)
            self.assertEqual(rehearsal["status"],"GREEN")
            self.assertEqual(rehearsal["verified_files"],1)
            self.assertFalse(rehearsal["live_restore_performed"])

    def test_rebuild_regenerates_only_derived_non_prod_state(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; inv.mkdir()
            (inv/"aion.json").write_text(json.dumps([{"company_id":"aion","knowledge_id":"k","kind":"KNOWLEDGE","source_type":"LIVE_SOURCE","source_uri":"https://example.com","state":"ACTIVE","content_hash":"x","provenance_id":"prv","confidence":1.0}]),encoding="utf-8")
            cfg=root/"companies.json"
            cfg.write_text(json.dumps([{"company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE","environment":"LAB","version":"1","interval_hours":24,"enabled":True}]),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(root/"ledger")
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(root/"rag")
            os.environ["CEREBRO_DIGITAL_TWIN_ROOT"]=str(root/"twin")
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            try: result=rebuild_company("aion","LAB")
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(result["status"],"GREEN")
            self.assertTrue(result["postcheck"]["rag_index"])
            self.assertTrue(result["postcheck"]["digital_twin"])
            self.assertFalse(result["prod_write_performed"])

    def test_prod_rebuild_requires_human(self):
        result=rebuild_company("fenix","PROD")
        self.assertEqual(result["status"],"HUMAN_REQUIRED")
        self.assertEqual(result["human_reason"],"HIGH_RISK")
        self.assertFalse(result["rebuild_performed"])

    def test_bcp_failover_is_only_declared_for_safe_non_prod_case(self):
        out=assess({"company_id":"aion","environment":"LAB","backup_ok":True,"rebuild_ok":True,"supervisor_ok":True,"critical_dependency_down":True,"known_safe_failover":True})
        self.assertEqual(out["status"],"READY")
        self.assertTrue(out["failover_allowed"])
        self.assertFalse(out["failover_performed"])
        prod=assess({"company_id":"fenix","environment":"PROD","backup_ok":True,"rebuild_ok":True,"supervisor_ok":True,"critical_dependency_down":True,"known_safe_failover":True})
        self.assertEqual(prod["status"],"HUMAN_REQUIRED")
        self.assertFalse(prod["failover_allowed"])

if __name__=="__main__": unittest.main()
