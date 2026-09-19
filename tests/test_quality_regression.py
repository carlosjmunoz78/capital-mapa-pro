import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.evaluate_qa_software_contract import evaluate_manifest
from jobs.evaluate_business_process_qa import evaluate_process
from jobs.run_regression_golden_suite import compare_case

class QualityRegressionTests(unittest.TestCase):
    def test_qa_requires_full_pyramid(self):
        layers={k:{"status":"GREEN","evidence_ref":f"e://{k}"} for k in ("unit","contract","integration","e2e","security","regression")}
        out=evaluate_manifest({"company_id":"aion","engine_id":"ENG-X","environment":"LAB","version":"1","layers":layers})
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["promotion_allowed"])
        layers.pop("e2e")
        out=evaluate_manifest({"company_id":"aion","engine_id":"ENG-X","environment":"LAB","version":"1","layers":layers})
        self.assertEqual(out["status"],"BLOCKED")
        self.assertIn("e2e",out["missing_layers"])

    def test_business_qa_generates_non_conformity_and_critical_human_exception(self):
        out=evaluate_process({
            "company_id":"fenix","process_id":"mortgage-file","environment":"LAB","version":"1",
            "checks":[
                {"check_id":"sla","status":"RED","severity":"HIGH","reason":"SLA_BREACH","evidence_ref":"e://sla"},
                {"check_id":"signature","status":"GREEN","severity":"CRITICAL","evidence_ref":"e://sig"}
            ]
        })
        self.assertEqual(out["status"],"NON_CONFORMITY")
        self.assertEqual(out["non_conformity_count"],1)
        out=evaluate_process({
            "company_id":"fenix","process_id":"mortgage-file","environment":"LAB","version":"1",
            "checks":[{"check_id":"critical","status":"RED","severity":"CRITICAL","reason":"CRITICAL_PROCESS_FAILURE"}]
        })
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["external_mutation_allowed"])

    def test_regression_case_detects_behavior_change(self):
        self.assertEqual(compare_case({"case_id":"x","expected":{"status":"ALLOW"},"actual":{"status":"ALLOW"}})["status"],"GREEN")
        self.assertEqual(compare_case({"case_id":"x","expected":{"status":"ALLOW"},"actual":{"status":"DENY"}})["status"],"REGRESSION")

if __name__=="__main__": unittest.main()
