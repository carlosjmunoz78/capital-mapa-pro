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


class ConsoleProposalQueueTests(unittest.TestCase):
    def test_queue_summary_and_console_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"evidence"; evidence.mkdir()
            config=root/"companies.json"
            config.write_text(json.dumps([{"company_id":"fenix","enabled":True}]),encoding="utf-8")
            (evidence/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","status":"PROPOSAL_READY","evidence_ref":"e://proposal",
                "facts":{"missing_required_sources":[],"failed_required_sources":[],"failed_optional_sources":[],
                         "source_status":{"business":{"status":"PROPOSAL_READY"}}}
            }),encoding="utf-8")
            queue_path=root/"queue.db"
            q=ProposalQueue(queue_path)
            q.upsert(ProposalRecord("fenix","p0","availability","SERVICE_HEALTH","LAB","1.0.0","app unavailable","e://app","LAB_DIAGNOSTIC_ONLY",False,0.0,"P0","WAITING_TEST"))
            q.upsert(ProposalRecord("fenix","p2","content","CONTENT","LAB","1.0.0","content check","e://content","LAB_DIAGNOSTIC_ONLY",False,0.0,"P2","WAITING_TEST"))
            summary=q.summary()
            self.assertEqual(summary["queued"],2)
            self.assertEqual(summary["priorities"]["P0"],1)
            self.assertEqual(summary["top"][0]["proposal_id"],"p0")
            q.close()

            output=root/"snapshot.json"
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE"]=str(queue_path)
            env["CEREBRO_IMPROVEMENT_CONSOLE_SNAPSHOT"]=str(output)
            subprocess.run(
                [sys.executable,str(ROOT/"cerebro-os/jobs/export_improvement_console_snapshot.py")],
                cwd=ROOT,env=env,text=True,capture_output=True,check=True
            )
            payload=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["proposal_queue"]["queued"],2)
            self.assertEqual(payload["proposal_queue"]["top"][0]["priority"],"P0")

    def test_missing_queue_exports_empty_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"e"; evidence.mkdir()
            config=root/"companies.json"
            config.write_text(json.dumps([]),encoding="utf-8")
            output=root/"snapshot.json"
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE"]=str(root/"missing.db")
            env["CEREBRO_IMPROVEMENT_CONSOLE_SNAPSHOT"]=str(output)
            subprocess.run([sys.executable,str(ROOT/"cerebro-os/jobs/export_improvement_console_snapshot.py")],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
            payload=json.loads(output.read_text())
            self.assertEqual(payload["proposal_queue"]["queued"],0)


if __name__=="__main__":
    unittest.main()
