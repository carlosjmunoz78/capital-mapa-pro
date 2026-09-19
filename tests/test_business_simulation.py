import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.simulate_business_rules import simulate,run

class BusinessSimulationTests(unittest.TestCase):
    def test_old_vs_new_replay_has_no_live_effect(self):
        result=simulate({
            "company_id":"aion","engine_id":"DEC-001","environment":"LAB","version":"1.0.0",
            "dataset_kind":"SYNTHETIC","events":[{"score":50},{"score":80},{"score":95}],
            "old_rule":{"field":"score","operator":"GE","value":90,"then_action":"ALLOW","else_action":"REVIEW"},
            "new_rule":{"field":"score","operator":"GE","value":80,"then_action":"ALLOW","else_action":"REVIEW"}
        })
        self.assertEqual(result["events_replayed"],3)
        self.assertEqual(result["changed_outcomes"],1)
        self.assertFalse(result["live_traffic_exposed"])
        self.assertFalse(result["external_mutation_allowed"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["production_ready"])

    def test_prod_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"never executes against PROD"):
            simulate({
                "company_id":"fenix","engine_id":"DEC-001","environment":"PROD","version":"1",
                "dataset_kind":"SYNTHETIC","events":[{"x":1}],
                "old_rule":{"field":"x","operator":"EQ","value":1},
                "new_rule":{"field":"x","operator":"EQ","value":2}
            })

    def test_live_secrets_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"live secrets"):
            simulate({
                "company_id":"fenix","engine_id":"DEC-001","environment":"LAB","version":"1",
                "dataset_kind":"ANONYMIZED","contains_live_secrets":True,"events":[{"x":1}],
                "old_rule":{"field":"x","operator":"EQ","value":1},
                "new_rule":{"field":"x","operator":"EQ","value":2}
            })

    def test_file_job_is_company_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            (src/"case1.json").write_text(json.dumps({
                "company_id":"aion","engine_id":"DEC-001","environment":"LAB","version":"1.0.0",
                "dataset_kind":"LAB_RECORDED","events":[{"x":1},{"x":2}],
                "old_rule":{"field":"x","operator":"GE","value":2,"then_action":"YES","else_action":"NO"},
                "new_rule":{"field":"x","operator":"GE","value":1,"then_action":"YES","else_action":"NO"}
            }),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_SIMULATION_CASE_ROOT"]=str(src); os.environ["CEREBRO_SIMULATION_RESULT_ROOT"]=str(out)
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((out/"aion.case1.json").read_text())
            self.assertEqual(p["company_id"],"aion")
            self.assertEqual(p["engine_id"],"SIM-001")

if __name__=="__main__": unittest.main()
