import re
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
        pushes=list(re.finditer(r'^\s*(?:run:\s*)?docker push "\$IMAGE"\s*$',text,re.MULTILINE))
        self.assertEqual(len(pushes),1,"exactly one image push command required")
        push=pushes[0].start()
        deploy=text.index("Deploy private Cloud Run PREPROD candidate")
        self.assertLess(smoke,push)
        self.assertLess(push,deploy)
        smoke_step=text[smoke:push]
        for marker in ("CEREBRO_PREPROD_MODE=persistent_candidate", "--network none", "http://127.0.0.1:8080/ready", "docker logs"):
            self.assertIn(marker,smoke_step)

    def test_deploy_requires_explicit_dispatch_and_preserves_private_candidate(self):
        if not WORKFLOW.exists():
            self.skipTest("workflow file intentionally absent from isolated runtime image")
        text=WORKFLOW.read_text(encoding="utf-8")
        deploy_job=text.split("  deploy-preprod:\n",1)[1]
        guard=re.search(r'^    if: (.+)$',deploy_job,re.MULTILINE)
        self.assertIsNotNone(guard)
        self.assertEqual(guard.group(1), "${{ vars.CEREBRO_FORGE_INTERNAL_CANARY_READY == 'true' && github.ref == 'refs/heads/cerebro-engine-factory-v0' && github.event_name == 'workflow_dispatch' && inputs.preflight_only == false }}")
        markers=("Verify private invoker and bounded queue before building", "Preserve exact PREPROD rollback revision", "Build image", "Push immutable image and pin exact registry digest", "Deploy private Cloud Run PREPROD candidate", "Invoke exact private candidate once", "Verify persistent remote onboarding rehearsal evidence", "Verify persistent PREPROD observability coverage", "Promote only fully accepted PREPROD revision")
        positions=[deploy_job.index(marker) for marker in markers]
        self.assertEqual(positions,sorted(positions))
        deploy_step=deploy_job[positions[4]:positions[5]]
        for marker in ('--image="$IMAGE_CANONICAL"', '--no-traffic', '--no-allow-unauthenticated', '--ingress=internal'):
            self.assertIn(marker,deploy_step)

if __name__=="__main__":
    unittest.main()
