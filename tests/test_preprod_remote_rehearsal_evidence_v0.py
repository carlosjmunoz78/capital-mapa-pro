import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github"/"workflows"/"cerebro-forge-preprod.yml"

class PreprodRemoteRehearsalEvidenceTests(unittest.TestCase):
    def test_workflow_persists_remote_rehearsal_evidence_and_keeps_prod_off(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Verify persistent remote onboarding rehearsal evidence",text)
        self.assertIn("PERSISTENT_REMOTE_ONBOARDING_REHEARSAL_PASS",text)
        self.assertIn("preprod-remote-onboarding-rehearsal.json",text)
        self.assertIn("synthetic_rehearsal",text)
        self.assertIn("browser_bridge_used",text)
        self.assertIn("computer_use_performed",text)
        self.assertIn("prod_claimed",text)
        self.assertIn("CEREBRO_EXTERNAL_WRITES=disabled",text)
        self.assertIn("CEREBRO_PROD_CREDENTIALS=disabled",text)

if __name__=="__main__":
    unittest.main()
