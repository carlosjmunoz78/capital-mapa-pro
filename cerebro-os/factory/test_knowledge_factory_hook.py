import json
import tempfile
import unittest
from pathlib import Path
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

if __name__ == '__main__':unittest.main()
