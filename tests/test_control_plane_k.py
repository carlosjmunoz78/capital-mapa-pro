import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.build_control_plane_snapshot import authorize,audit_secret_metadata,finops_guard,security_posture,observability_snapshot

class ControlPlaneTests(unittest.TestCase):
    def test_iam_denies_cross_company_and_missing_scope(self):
        ident={"identity_id":"agent-1","company_id":"fenix","scopes":["READ","EXECUTE"]}
        self.assertEqual(authorize(ident,company_id="aion",action_scope="READ")["decision"],"DENY")
        self.assertEqual(authorize(ident,company_id="fenix",action_scope="WRITE")["decision"],"DENY")
        self.assertEqual(authorize(ident,company_id="fenix",action_scope="EXECUTE")["decision"],"ALLOW")

    def test_secret_audit_never_accepts_values(self):
        out=audit_secret_metadata({"company_id":"fenix","secrets":[{"name":"API","provider":"github","location":"actions","scope":"COMPANY","value":"should-never-be-here"}]})
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"SECURITY_INCIDENT")
        self.assertFalse(out["secret_values_collected"])
        self.assertFalse(out["rotation_performed"])

    def test_finops_zero_cost_green_and_spend_human_required(self):
        green=finops_guard({"company_id":"aion","facts":{"estimated_additional_cost_eur":0,"latest_duration_seconds":100,"baseline_median_seconds":90}})
        self.assertEqual(green["status"],"GREEN")
        spend=finops_guard({"company_id":"aion","facts":{"estimated_additional_cost_eur":1,"latest_duration_seconds":100,"baseline_median_seconds":90}})
        self.assertEqual(spend["status"],"HUMAN_REQUIRED")
        self.assertEqual(spend["human_reason"],"MONEY_LIMIT")
        self.assertFalse(spend["automatic_spend_allowed"])

    def test_security_posture_consumes_red_and_incident_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); red=root/"red"; inc=root/"inc"; red.mkdir(); inc.mkdir()
            (red/"aion.json").write_text(json.dumps({"company_id":"aion","status":"GREEN"}),encoding="utf-8")
            (inc/"aion.json").write_text(json.dumps({"company_id":"aion","incidents":[]}),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_RED_TEAM_SUMMARY_ROOT"]=str(red); os.environ["CEREBRO_INCIDENT_ROOT"]=str(inc)
            try: out=security_posture("aion")
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(out["status"],"GREEN")
            self.assertFalse(out["policy_weakening_allowed"])

    def test_observability_missing_component_is_attention_not_fake_green(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=os.environ.copy()
            for key in ("CEREBRO_INCIDENT_ROOT","CEREBRO_SELF_HEAL_ROOT","CEREBRO_BACKUP_RESULT_ROOT","CEREBRO_REBUILD_RESULT_ROOT","CEREBRO_CONTINUITY_RESULT_ROOT","CEREBRO_CRISIS_ROOT"):
                os.environ[key]=str(root/key)
            try: out=observability_snapshot("aion","LAB","1")
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(out["status"],"ATTENTION")
            self.assertTrue(out["attention_components"])

if __name__=="__main__": unittest.main()
