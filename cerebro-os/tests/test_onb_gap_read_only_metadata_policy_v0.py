import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "identity"))
from read_only_browser_metadata_policy import (
    BrowserMetadataRequest, plan_read_only_metadata, verify_page_metadata,
)


class ReadOnlyMetadataPolicyTests(unittest.TestCase):
    def request(self, **overrides):
        params = dict(
            company_id="fenix", device_id="pc-lab", environment="LAB",
            version="v0", action="READ_ONLY_PAGE_METADATA",
            target_url="https://example.com/", policy_green=True,
            bridge_online=True, extension_fresh=True,
        )
        params.update(overrides)
        return BrowserMetadataRequest(**params)

    def receipt(self, **overrides):
        params = dict(
            status="COMPLETED", requested_url="https://example.com/",
            observed_url="https://example.com/", observed_title="Example Domain",
            page_load_complete=True, external_mutation_performed=False,
            secret_value_included=False, page_content_included=False,
        )
        params.update(overrides)
        return params

    def test_pilot_plan_is_metadata_only(self):
        plan = plan_read_only_metadata(self.request())
        self.assertEqual(plan["status"], "GREEN")
        self.assertFalse(plan["page_content_access"])
        self.assertFalse(plan["form_interaction"])
        self.assertFalse(plan["prod_activation_allowed"])
        self.assertTrue(plan["requires_extension_upgrade"])

    def test_redirect_is_not_semantically_verified(self):
        plan = plan_read_only_metadata(self.request())
        out = verify_page_metadata(plan, self.receipt(observed_url="https://other.example/"))
        self.assertFalse(out["semantic_verified"])

    def test_open_tab_without_readback_is_not_verified(self):
        plan = plan_read_only_metadata(self.request())
        out = verify_page_metadata(plan, self.receipt(observed_title="", page_load_complete=False))
        self.assertFalse(out["semantic_verified"])

    def test_full_metadata_receipt_is_verified(self):
        plan = plan_read_only_metadata(self.request())
        out = verify_page_metadata(plan, self.receipt())
        self.assertTrue(out["semantic_verified"])

    def test_scope_and_host_and_prod_are_denied(self):
        for request in (
            self.request(environment="PROD"),
            self.request(company_id="other"),
            self.request(target_url="https://example.com/login"),
            self.request(target_url="https://evil.test/"),
            self.request(higher_priority_connector=True),
            self.request(bridge_online=False),
        ):
            self.assertEqual(plan_read_only_metadata(request)["status"], "BLOCKED")

    def test_unexpected_content_or_secret_blocks_receipt(self):
        plan = plan_read_only_metadata(self.request())
        for receipt in (
            self.receipt(page_content_included=True),
            self.receipt(secret_value_included=True),
            self.receipt(external_mutation_performed=True),
        ):
            self.assertFalse(verify_page_metadata(plan, receipt)["semantic_verified"])


if __name__ == "__main__":
    unittest.main()
