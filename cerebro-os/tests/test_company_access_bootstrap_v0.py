import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"jobs"))

from jobs.bootstrap_company_access import bootstrap_company_access
from jobs.activate_company_engine_matrix import activate_matrix

class CompanyAccessBootstrapTests(unittest.TestCase):
    def test_existing_connector_satisfies_requirement_without_account_creation(self):
        out=bootstrap_company_access({
            "company_id":"fenix","environment":"LAB","version":"1.0.0",
            "requirements":[{"capability":"publish","purpose":"social","provider":"linkedin","required":True}],
            "existing_accounts":[],
            "existing_connectors":[{"company_id":"fenix","capability":"publish","active":True}],
            "session_observations":[],
        })
        self.assertEqual(out["status"],"GREEN")
        self.assertTrue(out["minimum_accesses_ready"])
        self.assertEqual(out["strategy"],"REUSE_DISCOVER_BEFORE_CREATE")
        self.assertFalse(out["account_creation_allowed"])
        self.assertFalse(out["secret_collection_allowed"])
        self.assertEqual(out["requirements"][0]["status"],"SATISFIED_EXISTING_CONNECTOR")

    def test_authenticated_session_can_be_discovered_without_secret_collection(self):
        out=bootstrap_company_access({
            "company_id":"fenix",
            "requirements":[{"capability":"research","purpose":"market","provider":"google","required":True}],
            "existing_accounts":[],
            "existing_connectors":[],
            "session_observations":[{"company_id":"fenix","provider":"google","authenticated":True}],
        })
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["requirements"][0]["status"],"AUTHENTICATED_SESSION_DISCOVERED")
        self.assertFalse(out["requirements"][0]["secret_value_required"])

    def test_missing_required_access_is_partial_and_routes_to_discovery(self):
        out=bootstrap_company_access({
            "company_id":"aion",
            "requirements":[{"capability":"publish","purpose":"social","provider":"linkedin","required":True}],
        })
        self.assertEqual(out["status"],"PARTIAL")
        self.assertFalse(out["minimum_accesses_ready"])
        self.assertEqual(out["missing_required_count"],1)
        self.assertEqual(out["next_stage"],"ACCOUNT_CONNECTOR_SESSION_DISCOVERY")
        self.assertFalse(out["external_mutation_allowed"])

    def test_raw_secret_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"raw secret field forbidden"):
            bootstrap_company_access({
                "company_id":"fenix",
                "requirements":[],
                "existing_accounts":[{"company_id":"fenix","password":"plaintext"}],
            })

    def test_cross_company_access_evidence_is_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            bootstrap_company_access({
                "company_id":"fenix",
                "requirements":[],
                "existing_connectors":[{"company_id":"aion","capability":"publish"}],
            })

    def test_engact_requires_access_bootstrap_evidence(self):
        base=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN"},
            {"company_id":"fenix","engine_id":"COMP-ONB-001","status":"GREEN"},
            {"company_id":"fenix","engine_id":"TENANT-001","status":"GREEN"},
            {"company_id":"fenix","engine_id":"OBSERV-001","status":"GREEN"},
            {"company_id":"fenix","engine_id":"DR-001","status":"GREEN"},
            {"company_id":"fenix","engine_id":"RBLD-001","status":"GREEN"},
        ]
        out=activate_matrix({"company_id":"fenix","engine_evidence":base})
        self.assertIn("ACCESSBOOT-001",out["blocked_required_engines"])

if __name__=="__main__":
    unittest.main()
