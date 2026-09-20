import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/".github"/"workflows"/"cerebro-forge-preprod.yml"

class PreprodDeployDiagnosticsTests(unittest.TestCase):
    def test_cloud_run_failure_captures_revision_and_logs_before_exit(self):
        if not WORKFLOW.exists():
            self.skipTest("workflow absent from isolated runtime image")
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Cloud Run deploy failed; collecting revision diagnostics",text)
        self.assertIn("gcloud run revisions list",text)
        self.assertIn("failed-revision.json",text)
        self.assertIn("failed-revision-logs.json",text)
        self.assertIn("gcloud logging read",text)
        self.assertIn('exit "$DEPLOY_RC"',text)

if __name__=="__main__":
    unittest.main()
