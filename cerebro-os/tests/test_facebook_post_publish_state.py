import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from facebook_post_publish_state import PostPublishInput, evaluate_post_publish


class FacebookPostPublishStateTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="facebook-publish",
            environment="PROD",
            version="1",
            publication_id="pub-1",
            run_id="run-1",
            receipt_confirmed=True,
            notion_return_ok=True,
            override_consumed=True,
            idempotency_committed=True,
            platform_state="PUBLISHED",
        )
        data.update(overrides)
        return PostPublishInput(**data)

    def test_all_green_opens_analytics(self):
        out = evaluate_post_publish(self.base())
        self.assertEqual(out["state"], "POST_PUBLISH_COMMITTED")
        self.assertTrue(out["analytics_windows_ready"])
        self.assertFalse(out["retry_publish_allowed"])

    def test_platform_pending_never_retries_publish(self):
        out = evaluate_post_publish(self.base(receipt_confirmed=False, platform_state="UPLOAD_ACCEPTED"))
        self.assertEqual(out["state"], "PLATFORM_CONFIRMATION_PENDING")
        self.assertFalse(out["analytics_windows_ready"])
        self.assertFalse(out["retry_publish_allowed"])

    def test_notion_return_blocks_commit(self):
        out = evaluate_post_publish(self.base(notion_return_ok=False, idempotency_committed=False))
        self.assertEqual(out["state"], "NOTION_RETURN_PENDING")
        self.assertEqual(out["idempotency_state"], "HOLD_UNTIL_NOTION_RETURN")
        self.assertFalse(out["analytics_windows_ready"])

    def test_override_must_be_consumed(self):
        out = evaluate_post_publish(self.base(override_consumed=False, idempotency_committed=False))
        self.assertEqual(out["state"], "OVERRIDE_CONSUMPTION_PENDING")
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "POLICY_CONFLICT")

    def test_idempotency_must_commit_before_analytics(self):
        out = evaluate_post_publish(self.base(idempotency_committed=False))
        self.assertEqual(out["state"], "IDEMPOTENCY_COMMIT_PENDING")
        self.assertFalse(out["analytics_windows_ready"])

    def test_wrong_environment_fail_closed(self):
        out = evaluate_post_publish(self.base(environment="TEST"))
        self.assertEqual(out["state"], "POST_PUBLISH_OUTSIDE_PROD")
        self.assertTrue(out["human_required"])
        self.assertFalse(out["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
