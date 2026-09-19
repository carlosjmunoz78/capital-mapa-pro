import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"identity"))

from identity.access_health import evaluate_access_health,access_recovery_plan
from jobs.build_access_health_snapshot import build_snapshot

class AccessHealthTests(unittest.TestCase):
    def _payload(self):
        return {
            "company_id":"fenix","environment":"LAB","version":"1.0.0",
            "accounts":[{"company_id":"fenix","account_id":"acct-1","status":"ACTIVE","environment":"LAB","evidence_ref":"e://acct"}],
            "sessions":[{"company_id":"fenix","account_id":"acct-1","authenticated":True,"environment":"LAB","evidence_ref":"e://sess"}],
            "credentials":[{"company_id":"fenix","account_id":"acct-1","environment":"LAB","secret_value_exposed":False,"evidence_ref":"e://cred"}],
            "connectors":[{"company_id":"fenix","account_id":"acct-1","environment":"LAB","evidence_ref":"e://conn"}],
            "bridge_heartbeats":[{"company_id":"fenix","environment":"LAB","profile_id":"chrome-1","online":True,"paired":True,"kill_switch_enabled":True,"evidence_ref":"e://hb"}],
        }

    def test_green_snapshot_requires_account_session_and_credential_reference(self):
        out=evaluate_access_health(**self._payload())
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["accounts_total"],1)
        self.assertEqual(out["authenticated_accounts"],1)
        self.assertEqual(out["credentialed_accounts"],1)
        self.assertEqual(out["online_bridge_profiles"],1)
        self.assertFalse(out["prod_actions_allowed"])

    def test_missing_session_and_credential_generate_safe_recovery_plan(self):
        payload=self._payload()
        payload["sessions"]=[]
        payload["credentials"]=[]
        out=evaluate_access_health(**payload)
        self.assertEqual(out["status"],"DEGRADED")
        kinds={x["type"] for x in out["issues"]}
        self.assertIn("AUTHENTICATED_SESSION_MISSING",kinds)
        self.assertIn("CREDENTIAL_REF_MISSING",kinds)
        plan=access_recovery_plan(out)
        actions={x["action"] for x in plan["safe_actions"]}
        self.assertIn("SESSION_DISCOVERY_OR_SAFE_RENEWAL",actions)
        self.assertIn("CREDENTIAL_REFERENCE_AUDIT",actions)

    def test_secret_exposure_escalates_security_incident(self):
        payload=self._payload()
        payload["credentials"][0]["secret_value_exposed"]=True
        out=evaluate_access_health(**payload)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"SECURITY_INCIDENT")
        plan=access_recovery_plan(out)
        self.assertEqual(plan["status"],"HUMAN_REQUIRED")
        self.assertIn("AUTONOMOUS_RECOVERY",plan["blocked_actions"])

    def test_cross_company_evidence_is_rejected(self):
        payload=self._payload()
        payload["sessions"][0]["company_id"]="aion"
        with self.assertRaisesRegex(ValueError,"cross-company session"):
            evaluate_access_health(**payload)

    def test_job_wraps_snapshot_with_access_health_engine_id(self):
        out=build_snapshot(self._payload())
        self.assertEqual(out["engine_id"],"ACCESS-HLT-001")
        self.assertEqual(out["status"],"GREEN")
        self.assertIn("recovery_plan",out)

if __name__=="__main__":
    unittest.main()
