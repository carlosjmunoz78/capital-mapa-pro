import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from registry import zeus_shared_catalog as z
from registry.canonical_loader import canonical_engine_ids

class ZeusSharedCatalog(unittest.TestCase):
    def test_actual_catalog(self):
        r=z.project_shared_catalog()
        self.assertEqual(r["logical_engine_count"],177)
        self.assertEqual(tuple(x["engine_id"] for x in r["engines"]),canonical_engine_ids())
        self.assertTrue(all(x["resource_owner"]=="ZEUS" and x["definition_shared"] for x in r["engines"]))
    def test_preserve_seed_metadata(self):
        r=z.project_shared_catalog()
        seed=json.loads(Path(z.__file__).with_name("engine_registry.seed.json").read_text())
        by_id={x["engine_id"]:x for x in r["engines"]}
        self.assertEqual(r["seed_record_count"],len(seed))
        for x in seed:
            self.assertEqual(by_id[x["engine_id"]]["existing_scope"],x["company_scope"])
            self.assertEqual(by_id[x["engine_id"]]["seed_status"],x["status"])
    def test_no_runtime_or_release_authority(self):
        r=z.project_shared_catalog()
        self.assertFalse(r["runtime_authorization_granted"])
        self.assertFalse(r["deployment_authorized"])
        self.assertTrue(all(x["execution_requires_scope"] and not x["runtime_verified_by_projection"] for x in r["engines"]))
    def test_unknown_or_duplicate_seed_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"seed.json"
            row={"engine_id":"FACT-001","company_scope":"GLOBAL_OR_SCOPED"}
            for rows in ([row,row],[{**row,"engine_id":"NOT-CANONICAL"}],[{**row,"company_scope":"UNRESTRICTED"}]):
                p.write_text(json.dumps(rows))
                with self.assertRaises(ValueError):z.project_shared_catalog(seed_path=p)
    def test_policy_drift_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"policy.json"
            data=json.loads(z.POLICY.read_text());data["grants_runtime_access"]=True
            p.write_text(json.dumps(data))
            with patch.object(z,"POLICY",p):
                with self.assertRaises(ValueError):z.project_shared_catalog()
