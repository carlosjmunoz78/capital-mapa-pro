import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.meta_experiment import build
from jobs.generate_meta_learning_experiments import run

class MetaExperimentTests(unittest.TestCase):
    def test_no_experiment_without_evidence_decision(self):
        self.assertIsNone(build({
            "decision":"MORE_EVIDENCE",
            "company_id":"aion","environment":"LAB","version":"1.0.0"
        }))

    def test_safe_candidate_never_auto_applies_or_weakens_gates(self):
        exp = build({
            "decision":"PROPOSE_META_EXPERIMENT",
            "company_id":"aion","environment":"LAB","version":"1.0.0",
            "bottleneck_stage":"EVALUATE",
            "prior_strategy_version":"meta-v0",
            "candidate_strategy_version":"meta-v0-candidate-1",
        })
        self.assertIsNotNone(exp)
        self.assertEqual(exp.action, "ADD_INDEPENDENT_EVALUATION_EVIDENCE")
        self.assertTrue(exp.independent_holdout_required)
        self.assertTrue(exp.judge_independence_required)
        self.assertFalse(exp.policy_weakening_allowed)
        self.assertFalse(exp.permission_escalation_allowed)
        self.assertFalse(exp.threshold_reduction_allowed)
        self.assertFalse(exp.auto_apply_allowed)
        self.assertFalse(exp.external_mutation_allowed)
        self.assertEqual(exp.cost_eur, 0.0)

    def test_job_outputs_candidate_only_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); meta=root/"meta"; out=root/"out"; meta.mkdir()
            (meta/"aion.json").write_text(json.dumps({
                "decision":"PROPOSE_META_EXPERIMENT",
                "company_id":"aion","environment":"LAB","version":"1.0.0",
                "bottleneck_stage":"TEST",
                "prior_strategy_version":"meta-v0",
                "candidate_strategy_version":"meta-v0-candidate-1",
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_META_LEARNING_ROOT"]=str(meta)
            os.environ["CEREBRO_META_EXPERIMENT_ROOT"]=str(out)
            try:
                run()
            finally:
                os.environ.clear(); os.environ.update(old)
            payload=json.loads((out/"aion.json").read_text())
            self.assertEqual(payload["status"],"CANDIDATE_ONLY")
            self.assertFalse(payload["production_ready"])
            self.assertFalse(payload["auto_apply_allowed"])
            self.assertIn("independent_holdout", payload["evidence_required"])

if __name__=="__main__":
    unittest.main()
