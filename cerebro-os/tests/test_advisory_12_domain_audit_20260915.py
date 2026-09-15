from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Advisory12DomainAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / "registry" / "advisory_12_domain_audit_20260915.json").read_text(encoding="utf-8"))
        cls.canonical = set(json.loads((ROOT / "registry" / "canonical_177.json").read_text(encoding="utf-8"))["engine_ids"])

    def test_exactly_12_unique_domains(self):
        domains = [row["domain"] for row in self.audit["domains"]]
        self.assertEqual(len(domains), 12)
        self.assertEqual(len(set(domains)), 12)
        self.assertEqual(self.audit["summary"]["domain_count"], 12)

    def test_no_invented_engine_ids(self):
        for row in self.audit["domains"]:
            for engine_id in row["canonical_engine_ids"]:
                self.assertIn(engine_id, self.canonical, f"{row['domain']} references non-canonical {engine_id}")

    def test_unmapped_domains_remain_explicitly_unmapped(self):
        unmapped = {row["domain"] for row in self.audit["domains"] if not row["canonical_engine_ids"]}
        self.assertEqual(unmapped, {"SUBVENCIONES_AYUDAS", "PATRIMONIAL"})
        for row in self.audit["domains"]:
            if row["domain"] in unmapped:
                self.assertEqual(row["audit_status"], "FALTA_MAPEO_CANONICO")
                self.assertEqual(row["capability_state"], "MAPPING_REQUIRED")

    def test_only_tax_is_seeded_as_advisory_domain_engine(self):
        seeded = {row["domain"] for row in self.audit["domains"] if row["registry_seeded"]}
        self.assertEqual(seeded, {"FISCAL"})

    def test_audit_does_not_claim_12_of_12_integration(self):
        self.assertFalse(self.audit["summary"]["fully_structured_and_integrated_12_of_12"])
        self.assertTrue(self.audit["rules"]["do_not_invent_engine_ids"])
        self.assertTrue(self.audit["rules"]["documentary_knowledge_is_not_capability"])


if __name__ == "__main__":
    unittest.main()
