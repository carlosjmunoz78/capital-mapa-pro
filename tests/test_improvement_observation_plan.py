import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.improvement_observation_plan import ObservationEnvelope, plan_stage_results


class ObservationPlanTests(unittest.TestCase):
    def test_no_change_is_full_noop_green(self):
        plan = plan_stage_results(ObservationEnvelope(
            "aion", True, "GITHUB_ENGINE_FACTORY", "e://green", "NO_CHANGE", 1.0, "healthy"
        ))
        self.assertEqual(len(plan), 12)
        self.assertTrue(all(x.status == "GREEN" for x in plan.values()))

    def test_proposal_stops_at_lab_waiting(self):
        plan = plan_stage_results(ObservationEnvelope(
            "aion", True, "GITHUB_ENGINE_FACTORY", "e://failure", "PROPOSAL_READY", 1.0, "failure"
        ))
        self.assertEqual(plan["PROPOSE"].status, "GREEN")
        self.assertEqual(plan["LAB"].status, "WAITING")

    def test_low_confidence_requires_human(self):
        plan = plan_stage_results(ObservationEnvelope(
            "aion", True, "SOURCE", "e://weak", "NO_CHANGE", 0.4, "weak"
        ))
        self.assertEqual(plan["DETECT"].status, "HUMAN_REQUIRED")
        self.assertEqual(plan["DETECT"].human_reason, "LOW_CONFIDENCE")

    def test_entrypoint_consumes_checked_observation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root/"companies.json"
            cfg.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            evidence = root/"evidence"; evidence.mkdir()
            (evidence/"aion.observations.json").write_text(json.dumps({
                "company_id":"aion","checked":True,"source":"GITHUB_ENGINE_FACTORY",
                "evidence_ref":"e://green","status":"NO_CHANGE","confidence":1.0,"summary":"healthy"
            }), encoding="utf-8")
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_NOW"]="2026-09-19T12:00:00+00:00"
            proc=subprocess.run(
                [sys.executable,str(ROOT/"cerebro-os/jobs/continuous_improvement_entrypoint.py")],
                cwd=ROOT,env=env,text=True,capture_output=True,check=True
            )
            out=json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(out["status"],"GREEN")
            self.assertEqual(out["green"],1)

    def test_envelope_accepts_aggregated_facts(self):
        plan = plan_stage_results(ObservationEnvelope(
            "aion", True, "MULTI_SOURCE", "e://multi", "NO_CHANGE", 1.0, "healthy",
            {"required_sources": ["technical"], "failed_optional_sources": []},
        ))
        self.assertEqual(plan["OBSERVE"].status, "GREEN")


if __name__=="__main__":
    unittest.main()
