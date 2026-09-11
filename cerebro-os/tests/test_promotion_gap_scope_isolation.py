import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("promotion_gap_scope", ROOT / "registry/promotion_gap_queue.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["promotion_gap_scope"] = mod
spec.loader.exec_module(mod)


def refs(company="fenix", environment="PROD", version="2.0.0"):
    result = {gate: f"e:{gate}" for gate in mod.REQUIRED_GATES}
    result.update({"company_id": company, "environment": environment, "version": version})
    return result


class PromotionGapScopeIsolationTests(unittest.TestCase):
    def test_exact_scope_can_be_ready_for_gate(self):
        evidence = {"FACT-001": refs()}
        self.assertEqual(("FACT-001",), mod.ready_for_gate(canonical_ids=("FACT-001",), company_id="fenix", target_environment="PROD", target_version="2.0.0", evidence_by_engine=evidence))

    def test_other_company_environment_or_version_stays_blocked(self):
        for evidence in (
            {"FACT-001": refs(company="other")},
            {"FACT-001": refs(environment="PREPROD")},
            {"FACT-001": refs(version="1.0.0")},
        ):
            queue = mod.build_promotion_gap_queue(canonical_ids=("FACT-001",), company_id="fenix", target_environment="PROD", target_version="2.0.0", evidence_by_engine=evidence)
            self.assertEqual("PROMOTION_SCOPE_MISMATCH", queue[0]["state"])

    def test_plain_gate_refs_without_scope_cannot_false_green(self):
        evidence = {"FACT-001": {gate: f"e:{gate}" for gate in mod.REQUIRED_GATES}}
        queue = mod.build_promotion_gap_queue(canonical_ids=("FACT-001",), company_id="fenix", target_environment="PROD", target_version="2.0.0", evidence_by_engine=evidence)
        self.assertEqual("PROMOTION_SCOPE_MISMATCH", queue[0]["state"])


if __name__ == "__main__":
    unittest.main()
