import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from factory import scaffold
from knowledge_factory_hook import knowledge_manifest, write_knowledge_scaffold, register_agent_candidate

ENGINE = {"engine_id":"TEST-001", "environment":"LAB", "version":"0.1.0"}

class TestKnowledgeHook(unittest.TestCase):
    def test_scaffold_and_agent(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/"engines"/"TEST-001"
            write_knowledge_scaffold(target, ENGINE, "fenix-capital")
            a=json.loads((target/"training"/"knowledge_factory_enrollment.json").read_text())
            self.assertEqual(a["company_id"],"UNRESOLVED_TRUSTED_FACTORY_CONTEXT")
            self.assertEqual(a["unverified_company_claim"],"fenix-capital")
            self.assertFalse(a["security"]["production_enabled"])
            e=json.loads((target/"events"/"KNOWLEDGE_ENROLLMENT_REQUESTED.contract.json").read_text())
            self.assertFalse(e["dispatch_enabled"])
            p=register_agent_candidate(target,"SEO-AGENT", "SEO-SA-001")
            self.assertEqual(p,register_agent_candidate(target,"SEO-AGENT", "SEO-SA-001"))
            self.assertFalse(json.loads(p.read_text())["permissions_granted"])
            self.assertIsNotNone(register_agent_candidate(target,"SEO-PF01:DIRECTOR", "SEO-D01:SPECIALIST:01"))
            with self.assertRaises(FileExistsError):write_knowledge_scaffold(target,ENGINE)
    def test_reject_prod_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):knowledge_manifest({"engine_id":"TEST-001","environment":"PROD","version":"0.1.0"})
            with self.assertRaises(ValueError):write_knowledge_scaffold(Path(root),ENGINE,"../other-company")
            target=Path(root)/"TEST-001"
            write_knowledge_scaffold(target, ENGINE)
            with self.assertRaises(ValueError):register_agent_candidate(target,"../private")
            with self.assertRaises(ValueError):register_agent_candidate(target,"OK","../../../etc")
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/"TEST-001"
            write_knowledge_scaffold(target, ENGINE)
            p=register_agent_candidate(target,"A1")
            p.write_text("conflict")
            with self.assertRaises(FileExistsError):register_agent_candidate(target,"A1")

    def test_factory_emits_candidates_only_for_explicit_identities(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {}, clear=True):
            target = scaffold(Path(root), "TEST-001", "Test", agent_inventory=[
                {"agent_id": "AGT-1"},
                {"agent_id": "AGT-1", "subagent_id": "AGT-1:SUB"},
                {"agent_id": "AGT-1"},
            ])
            candidates = [json.loads(path.read_text()) for path in
                          (target / "training" / "knowledge_candidates").glob("*.json")]
            self.assertEqual(len(candidates), 2)
            self.assertTrue(all(not item["permissions_granted"] and
                                not item["dispatch_enabled"] for item in candidates))
            with self.assertRaises(ValueError):
                scaffold(Path(root), "TEST-002", "Test", agent_inventory=[{"agent_id": "../invalid"}])
            self.assertFalse((Path(root) / "engines" / "TEST-002").exists())

    def test_ums_scaffold_links_source_profile_without_enabling_consumption(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {}, clear=True):
            target = scaffold(Path(root), "UMS-001", "Productora LAB",
                              agent_inventory=[{"agent_id": "TEST-ONLY", "subagent_id": "QA-1"}])
            enrollment = json.loads((target / "training" / "knowledge_factory_enrollment.json").read_text())
            self.assertEqual(enrollment["source_registry_ref"],
                             "cerebro-os/knowledge/appsscript_lab_v0/ums001_source_profile.lab.json")
            self.assertEqual(enrollment["company_id"], "UNRESOLVED_TRUSTED_FACTORY_CONTEXT")
            candidate = register_agent_candidate(target, "TEST-ONLY", "QA-1")
            self.assertEqual(len(list(candidate.parent.glob("*.json"))), 1)
            record = json.loads(candidate.read_text())
            self.assertFalse(record["permissions_granted"])
            self.assertFalse(record["dispatch_enabled"])
            self.assertFalse(record["gateway_consumed"])

if __name__ == '__main__':unittest.main()
