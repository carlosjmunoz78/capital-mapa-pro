import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.build_continuity_cases_from_runtime import run

class ContinuityCaseBuilderTests(unittest.TestCase):
    def test_runtime_results_become_company_scoped_case(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"cfg.json"; b=root/"b"; r=root/"r"; i=root/"i"; out=root/"out"
            b.mkdir(); r.mkdir(); i.mkdir()
            cfg.write_text(json.dumps([{"company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE","environment":"LAB","version":"1","interval_hours":24,"enabled":True}]),encoding="utf-8")
            (b/"aion.json").write_text(json.dumps({"company_id":"aion","status":"GREEN"}),encoding="utf-8")
            (r/"aion.json").write_text(json.dumps({"company_id":"aion","status":"GREEN"}),encoding="utf-8")
            (i/"aion.json").write_text(json.dumps({"company_id":"aion","status":"GREEN","incidents":[]}),encoding="utf-8")
            old=os.environ.copy()
            os.environ.update({"CEREBRO_IMPROVEMENT_COMPANIES":str(cfg),"CEREBRO_BACKUP_RESULT_ROOT":str(b),"CEREBRO_REBUILD_RESULT_ROOT":str(r),"CEREBRO_INCIDENT_ROOT":str(i),"CEREBRO_CONTINUITY_CASE_ROOT":str(out)})
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((out/"aion.json").read_text())
            self.assertTrue(p["backup_ok"]); self.assertTrue(p["rebuild_ok"]); self.assertTrue(p["supervisor_ok"])
            self.assertFalse(p["known_safe_failover"])
            self.assertFalse(p["external_mutation_allowed"])
if __name__=="__main__": unittest.main()
