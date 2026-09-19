import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.generate_factory_supervisor_self_improvement import run, target_engine


class FactorySupervisorSelfImprovementTests(unittest.TestCase):
    def test_routes_test_coverage_to_factory(self):
        self.assertEqual(target_engine("ADD_CONTRACT_TEST_COVERAGE"), "FACT-001")

    def test_routes_observation_to_supervisor(self):
        self.assertEqual(target_engine("INCREASE_OBSERVATION_COVERAGE"), "SUP-001")

    def test_candidate_stays_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"meta"; out=root/"out"; src.mkdir()
            (src/"aion.json").write_text(json.dumps({
                "record_type":"meta_experiment_spec",
                "status":"CANDIDATE_ONLY",
                "company_id":"aion","environment":"LAB","version":"1.0.0",
                "experiment_id":"aion:LAB:1.0.0:TEST:meta-v1",
                "action":"ADD_CONTRACT_TEST_COVERAGE",
                "independent_holdout_required":True,
                "judge_independence_required":True,
                "policy_weakening_allowed":False,
                "permission_escalation_allowed":False,
                "threshold_reduction_allowed":False,
                "auto_apply_allowed":False,
                "external_mutation_allowed":False
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_META_EXPERIMENT_ROOT"]=str(src)
            os.environ["CEREBRO_SELF_IMPROVEMENT_ROOT"]=str(out)
            try:
                run()
            finally:
                os.environ.clear(); os.environ.update(old)
            payload=json.loads((out/"aion.fact-001.json").read_text())
            self.assertEqual(payload["engine_id"],"FACT-001")
            self.assertEqual(payload["status"],"CANDIDATE_ONLY")
            self.assertFalse(payload["auto_apply_allowed"])
            self.assertFalse(payload["external_mutation_allowed"])
            self.assertFalse(payload["policy_change_allowed"])
            self.assertFalse(payload["permission_change_allowed"])
            self.assertFalse(payload["judge_change_allowed"])
            self.assertFalse(payload["budget_change_allowed"])
            self.assertTrue(payload["requires_factory_versioning"])
            self.assertIn("backup_rebuild",payload["required_gates"])

    def test_rejects_gate_weakening(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"meta"; out=root/"out"; src.mkdir()
            (src/"aion.json").write_text(json.dumps({
                "status":"CANDIDATE_ONLY",
                "company_id":"aion","environment":"LAB","version":"1.0.0",
                "action":"IMPROVE_MEASUREMENT_FIDELITY",
                "independent_holdout_required":True,
                "judge_independence_required":True,
                "policy_weakening_allowed":True,
                "permission_escalation_allowed":False,
                "threshold_reduction_allowed":False,
                "auto_apply_allowed":False,
                "external_mutation_allowed":False
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_META_EXPERIMENT_ROOT"]=str(src)
            os.environ["CEREBRO_SELF_IMPROVEMENT_ROOT"]=str(out)
            try:
                with self.assertRaisesRegex(ValueError,"policy weakening"):
                    run()
            finally:
                os.environ.clear(); os.environ.update(old)


if __name__=="__main__":
    unittest.main()
