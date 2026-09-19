import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.generate_improvement_lab_proposals import generate, build_lab_evidence


class ImprovementProposalLabTests(unittest.TestCase):
    def test_proposal_ready_source_creates_zero_cost_no_mutation_lab_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"evidence"; evidence.mkdir()
            proposals=root/"proposals"
            config=root/"companies.json"
            config.write_text(json.dumps([{
                "company_id":"fenix","legal_name":"Fenix Capital",
                "autonomy_profile":"FENIX_SENSITIVE","environment":"LAB",
                "version":"1.0.0","interval_hours":24,"enabled":True
            }]),encoding="utf-8")
            (evidence/"fenix.business.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"OFFICIAL_PUBLIC_WEB",
                "evidence_ref":"https://example.com/#sha256=x","status":"PROPOSAL_READY",
                "confidence":0.95,"summary":"missing schema"
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_PROPOSALS_ROOT"]=str(proposals)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            try:
                generate(); build_lab_evidence()
            finally:
                os.environ.clear(); os.environ.update(old)
            lab=json.loads((evidence/"fenix.lab.json").read_text())
            self.assertEqual(lab["status"],"GREEN")
            self.assertFalse(lab["external_mutation_allowed"])
            self.assertEqual(lab["cost_eur"],0.0)
            self.assertEqual(lab["proposals"][0]["action"],"LAB_DIAGNOSTIC_ONLY")
            self.assertFalse(lab["proposals"][0]["external_mutation_allowed"])

    def test_entrypoint_advances_proposal_through_lab_then_waits_at_test(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"evidence"; evidence.mkdir()
            config=root/"companies.json"
            config.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION",
                "autonomy_profile":"AUTONOMOUS_VENTURE","environment":"LAB",
                "version":"1.0.0","interval_hours":24,"enabled":True
            }]),encoding="utf-8")
            (evidence/"aion.observations.json").write_text(json.dumps({
                "company_id":"aion","checked":True,"source":"MULTI_SOURCE",
                "evidence_ref":"e://proposal","status":"PROPOSAL_READY","confidence":1.0,
                "summary":"candidate found","facts":{}
            }),encoding="utf-8")
            (evidence/"aion.lab.json").write_text(json.dumps({
                "company_id":"aion","stage":"LAB","status":"GREEN","evidence_ref":"e://lab",
                "external_mutation_allowed":False,"cost_eur":0.0,"proposals":[]
            }),encoding="utf-8")
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_NOW"]="2026-09-19T12:00:00+00:00"
            proc=subprocess.run(
                [sys.executable,str(ROOT/"cerebro-os/jobs/continuous_improvement_entrypoint.py")],
                cwd=ROOT,env=env,text=True,capture_output=True,check=True
            )
            out=json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(out["status"],"WAITING")
            self.assertEqual(out["waiting"],1)
            checkpoint=root/"state"/"state"/"aion"/"LAB"/"1.0.0"/"checkpoint.db"
            self.assertTrue(checkpoint.exists())


if __name__=="__main__":
    unittest.main()
