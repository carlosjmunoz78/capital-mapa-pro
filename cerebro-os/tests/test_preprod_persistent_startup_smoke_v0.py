import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/".github"/"workflows"/"cerebro-forge-preprod.yml"

class PreprodPersistentStartupSmokeTests(unittest.TestCase):
    def test_persistent_candidate_is_smoked_before_push_and_deploy(self):
        if not WORKFLOW.exists():
            self.skipTest("workflow file intentionally absent from isolated runtime image")
        text=WORKFLOW.read_text(encoding="utf-8")
        smoke=text.index("Persistent candidate startup smoke before push")
        push=text.index('docker push "$IMAGE"')
        deploy=text.index("Deploy private Cloud Run PREPROD candidate")
        self.assertLess(smoke,push)
        self.assertLess(push,deploy)
        # The PREPROD service must not receive new traffic before all existing gates pass.
        promote=text.index("Promote only fully accepted PREPROD revision")
        observability=text.index("Verify persistent PREPROD observability coverage")
        self.assertLess(deploy,observability)
        self.assertLess(observability,promote)
        self.assertIn("--no-traffic",text)
        self.assertIn("--to-revisions",text)
        self.assertIn("IMAGE_CANONICAL",text)
        self.assertIn("application/vnd.oci.image.index.v1+json",text)
        self.assertIn("single linux/amd64 child of pinned OCI index",text)
        self.assertIn("PREVIOUS_REVISION",text)
        self.assertIn("cancel-in-progress: false",text)
        self.assertIn("GITHUB_RUN_ATTEMPT",text)
        self.assertIn("CEREBRO_PREPROD_MODE=persistent_candidate",text)
        self.assertIn("--network none",text)
        self.assertIn("http://127.0.0.1:8080/ready",text)
        self.assertIn("docker logs",text)

if __name__=="__main__":
    unittest.main()
