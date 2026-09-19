import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.generate_red_team_synthetic_cases import run as generate_run
from jobs.run_adversarial_evaluation import run as evaluate_run
from jobs.verify_red_team_daily_results import run as verify_run

class RedDailyCasesTests(unittest.TestCase):
    def test_full_synthetic_suite_is_blocked_as_expected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"companies.json"
            cases=root/"cases"; results=root/"results"; summary=root/"summary"
            cfg.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_RED_TEAM_CASE_ROOT"]=str(cases)
            os.environ["CEREBRO_RED_TEAM_RESULT_ROOT"]=str(results)
            os.environ["CEREBRO_RED_TEAM_SUMMARY_ROOT"]=str(summary)
            try:
                generate_run()
                evaluate_run()
                verify_run()
            finally:
                os.environ.clear(); os.environ.update(old)
            files=list(cases.glob("*.json"))
            self.assertEqual(len(files),6)
            p=json.loads((summary/"aion.json").read_text())
            self.assertEqual(p["status"],"GREEN")
            self.assertEqual(p["cases"],6)
            self.assertEqual(p["blocked_as_expected"],6)
            self.assertEqual(p["unexpected_green"],0)
            self.assertFalse(p["external_mutation_allowed"])

    def test_prod_company_generates_no_offensive_cases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"companies.json"; cases=root/"cases"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","legal_name":"Fenix","autonomy_profile":"FENIX_SENSITIVE",
                "environment":"PROD","version":"1.0.0","interval_hours":24,"enabled":True
            }]),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_RED_TEAM_CASE_ROOT"]=str(cases)
            try: generate_run()
            finally: os.environ.clear(); os.environ.update(old)
            self.assertEqual(list(cases.glob("*.json")),[])

if __name__=="__main__": unittest.main()
