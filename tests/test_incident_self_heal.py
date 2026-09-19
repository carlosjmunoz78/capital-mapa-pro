import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.detect_runtime_incidents import detect_for_company
from jobs.execute_preapproved_self_heal import run as heal_run

class IncidentSelfHealTests(unittest.TestCase):
    def test_missing_derived_artifacts_create_known_incidents(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; inv.mkdir()
            (inv/"aion.json").write_text("[]",encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(root/"rag")
            os.environ["CEREBRO_DIGITAL_TWIN_ROOT"]=str(root/"twin")
            os.environ["CEREBRO_RED_TEAM_SUMMARY_ROOT"]=str(root/"red")
            os.environ["CEREBRO_REGRESSION_ROOT"]=str(root/"reg")
            os.environ["CEREBRO_PROCESS_QA_RESULT_ROOT"]=str(root/"process")
            try: out=detect_for_company("aion","LAB","1")
            finally: os.environ.clear(); os.environ.update(old)
            kinds={x["incident_type"] for x in out["incidents"]}
            self.assertIn("RAG_INDEX_MISSING",kinds)
            self.assertIn("TWIN_SNAPSHOT_MISSING",kinds)
            self.assertTrue(all(x["preapproved_repair_id"] for x in out["incidents"]))

    def test_security_regression_is_human_required_not_auto_fixed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); red=root/"red"; red.mkdir()
            (red/"fenix.json").write_text(json.dumps({"company_id":"fenix","status":"RED"}),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(root/"inv")
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(root/"rag")
            os.environ["CEREBRO_DIGITAL_TWIN_ROOT"]=str(root/"twin")
            os.environ["CEREBRO_RED_TEAM_SUMMARY_ROOT"]=str(red)
            os.environ["CEREBRO_REGRESSION_ROOT"]=str(root/"reg")
            os.environ["CEREBRO_PROCESS_QA_RESULT_ROOT"]=str(root/"process")
            try: out=detect_for_company("fenix","LAB","1")
            finally: os.environ.clear(); os.environ.update(old)
            sec=[x for x in out["incidents"] if x["incident_type"]=="SECURITY_REGRESSION"][0]
            self.assertEqual(sec["status"],"HUMAN_REQUIRED")
            self.assertEqual(sec["human_reason"],"SECURITY_INCIDENT")
            self.assertIsNone(sec["preapproved_repair_id"])

    def test_preapproved_local_repairs_execute_and_postcheck(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            inc=root/"inc"; inv=root/"inv"; rag=root/"rag"; twin=root/"twin"; out=root/"heal"
            inc.mkdir(); inv.mkdir()
            (inv/"aion.json").write_text(json.dumps([{"company_id":"aion","knowledge_id":"k","kind":"KNOWLEDGE","source_type":"LIVE_SOURCE","source_uri":"https://example.com","state":"ACTIVE","content_hash":"x","provenance_id":"prv","confidence":1.0}]),encoding="utf-8")
            cfg=root/"companies.json"
            cfg.write_text(json.dumps([{"company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE","environment":"LAB","version":"1","interval_hours":24,"enabled":True}]),encoding="utf-8")
            (inc/"aion.json").write_text(json.dumps({
              "company_id":"aion","environment":"LAB","incidents":[
                {"incident_id":"i1","company_id":"aion","preapproved_repair_id":"REBUILD_RAG_INDEX","human_reason":None}
              ]
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_INCIDENT_ROOT"]=str(inc)
            os.environ["CEREBRO_SELF_HEAL_ROOT"]=str(out)
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(root/"ledger")
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(rag)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_DIGITAL_TWIN_ROOT"]=str(twin)
            try: heal_run()
            finally: os.environ.clear(); os.environ.update(old)
            result=json.loads((out/"aion.json").read_text())
            self.assertEqual(result["repairs"][0]["status"],"FIXED")
            self.assertTrue((rag/"aion.json").exists())
            self.assertTrue(result["preapproved_only"])
            self.assertFalse(result["external_mutation_allowed"])

    def test_prod_known_incident_does_not_auto_repair(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inc=root/"inc"; out=root/"heal"; inc.mkdir()
            (inc/"fenix.json").write_text(json.dumps({
              "company_id":"fenix","environment":"PROD","incidents":[
                {"incident_id":"i1","company_id":"fenix","preapproved_repair_id":"REBUILD_RAG_INDEX","human_reason":None}
              ]
            }),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_INCIDENT_ROOT"]=str(inc); os.environ["CEREBRO_SELF_HEAL_ROOT"]=str(out)
            try: heal_run()
            finally: os.environ.clear(); os.environ.update(old)
            result=json.loads((out/"fenix.json").read_text())
            self.assertEqual(result["repairs"][0]["status"],"HUMAN_REQUIRED")
            self.assertEqual(result["repairs"][0]["human_reason"],"HIGH_RISK")

if __name__=="__main__": unittest.main()
