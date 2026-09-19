import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsoleSnapshotTests(unittest.TestCase):
    def test_snapshot_exports_company_attention(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            evidence.mkdir()
            config = root / "companies.json"
            config.write_text(json.dumps([
                {"company_id":"aion","enabled":True},
                {"company_id":"fenix","enabled":True}
            ]), encoding="utf-8")
            (evidence/"aion.observations.json").write_text(json.dumps({
                "company_id":"aion","status":"NO_CHANGE","evidence_ref":"e://aion",
                "facts":{"missing_required_sources":[],"failed_required_sources":[],"failed_optional_sources":[],
                         "source_status":{"technical":{"status":"NO_CHANGE"}}}
            }),encoding="utf-8")
            (evidence/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","status":"PROPOSAL_READY","evidence_ref":"e://fenix",
                "facts":{"missing_required_sources":[],"failed_required_sources":[],"failed_optional_sources":[],
                         "source_status":{"technical":{"status":"NO_CHANGE"},"business":{"status":"PROPOSAL_READY"}}}
            }),encoding="utf-8")
            output=root/"snapshot.json"
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_CONSOLE_SNAPSHOT"]=str(output)
            proc=subprocess.run(
                [sys.executable,str(ROOT/"cerebro-os/jobs/export_improvement_console_snapshot.py")],
                cwd=ROOT,env=env,text=True,capture_output=True,check=True
            )
            payload=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["service"],"continuous-improvement-sources")
            self.assertEqual(payload["status"],"PROPOSAL_READY")
            self.assertEqual(payload["attention_company_ids"],["fenix"])
            self.assertEqual(payload["count"],2)
            self.assertTrue(proc.stdout.strip())

    def test_disabled_company_not_exported(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"e"; evidence.mkdir()
            config=root/"companies.json"
            config.write_text(json.dumps([{"company_id":"off","enabled":False}]),encoding="utf-8")
            output=root/"snapshot.json"
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_CONSOLE_SNAPSHOT"]=str(output)
            subprocess.run([sys.executable,str(ROOT/"cerebro-os/jobs/export_improvement_console_snapshot.py")],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
            payload=json.loads(output.read_text())
            self.assertEqual(payload["count"],0)
            self.assertEqual(payload["status"],"GREEN")


if __name__=="__main__":
    unittest.main()
