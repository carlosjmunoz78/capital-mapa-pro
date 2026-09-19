import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from learning.improvement_proposal_queue import ProposalQueue, ProposalRecord
from jobs.generate_improvement_candidate_tests import generate


class CandidateTestGenerationTests(unittest.TestCase):
    def test_candidate_contract_test_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            queue_path=root/"queue.db"
            q=ProposalQueue(queue_path)
            q.upsert(ProposalRecord(
                "fenix","p1","business","WEB_SEO","LAB","1.0.0",
                "missing_canonical","https://example.com/#sha256=x","LAB_DIAGNOSTIC_ONLY",
                False,0.0,"P1","WAITING_TEST"
            ))
            q.close()
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE"]=str(queue_path)
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"]=str(root/"candidates")
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root/"evidence")
            try:
                generate()
            finally:
                os.environ.clear(); os.environ.update(old)
            candidate=json.loads((root/"candidates/fenix.json").read_text())
            self.assertEqual(candidate["candidates"][0]["mode"],"DETERMINISTIC_PATCH_SPEC")
            self.assertEqual(candidate["candidates"][0]["change_spec"]["operation"],"SET_CANONICAL")
            test=json.loads((root/"evidence/fenix.test.json").read_text())
            self.assertEqual(test["status"],"GREEN")
            self.assertEqual(test["test_scope"],"CANDIDATE_CONTRACT_ONLY")
            self.assertFalse(test["external_mutation_allowed"])
            self.assertEqual(test["cost_eur"],0.0)

    def test_runtime_advances_through_test_then_waits_at_evaluate(self):
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
                "external_mutation_allowed":False,"cost_eur":0.0
            }),encoding="utf-8")
            (evidence/"aion.test.json").write_text(json.dumps({
                "company_id":"aion","stage":"TEST","status":"GREEN","evidence_ref":"e://test",
                "test_scope":"CANDIDATE_CONTRACT_ONLY","external_mutation_allowed":False,"cost_eur":0.0
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

    def test_only_highest_priority_proposal_per_company_is_generated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            queue_path=root/"queue.db"
            q=ProposalQueue(queue_path)
            q.upsert(ProposalRecord(
                "fenix","low","content","CONTENT","LAB","1.0.0",
                "content issue","e://content","LAB_DIAGNOSTIC_ONLY",False,0.0,"P2","WAITING_TEST"
            ))
            q.upsert(ProposalRecord(
                "fenix","high","availability","SERVICE_HEALTH","LAB","1.0.0",
                "app unavailable","e://app","LAB_DIAGNOSTIC_ONLY",False,0.0,"P0","WAITING_TEST"
            ))
            q.close()
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE"]=str(queue_path)
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"]=str(root/"candidates")
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root/"evidence")
            try:
                generate()
            finally:
                os.environ.clear(); os.environ.update(old)
            payload=json.loads((root/"candidates/fenix.json").read_text())
            self.assertEqual(len(payload["candidates"]),1)
            self.assertEqual(payload["candidates"][0]["proposal_id"],"high")


if __name__=="__main__":
    unittest.main()
