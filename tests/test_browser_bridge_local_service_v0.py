import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from identity.browser_bridge_local_service import (
    bootstrap_device_id,load_state,pair_state,heartbeat_state,safe_public_state
)

class BrowserBridgeLocalServiceTests(unittest.TestCase):
    def test_pairing_persists_safe_local_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"state.json"
            state=pair_state(
              path=path,company_id="fenix",profile_id="chrome-default",
              browser_family="CHROME",environment="LAB",version="v0",
            )
            self.assertTrue(state["paired"])
            self.assertTrue(state["online"])
            self.assertTrue(state["kill_switch_enabled"])
            self.assertEqual(state["cloud_transport_status"],"NOT_CONFIGURED")
            self.assertFalse(state["cloud_transport_configured"])
            reread=load_state(path)
            self.assertEqual(reread["company_id"],"fenix")
            self.assertEqual(reread["profile_id"],"chrome-default")

    def test_prod_pairing_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"LAB/PREPROD"):
                pair_state(
                  path=Path(tmp)/"state.json",company_id="fenix",profile_id="chrome",
                  browser_family="CHROME",environment="PROD",version="v0",
                )

    def test_secret_fields_are_not_part_of_public_state(self):
        public=safe_public_state({
          "device_id":"d","company_id":"fenix","profile_id":"p","browser_family":"CHROME",
          "environment":"LAB","version":"v0","paired":True,"online":True,
          "kill_switch_enabled":True,"last_seen_at":1,
          "cloud_transport_configured":False,"cloud_transport_status":"NOT_CONFIGURED",
          "password":"must-not-leak",
        })
        self.assertNotIn("password",public)

    def test_heartbeat_bootstraps_device_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"state.json"
            state=heartbeat_state(path)
            self.assertTrue(state["device_id"].startswith("desktop-"))
            self.assertGreaterEqual(state["last_seen_at"],0)

    def test_device_id_is_stable_shape(self):
        value=bootstrap_device_id()
        self.assertTrue(value.startswith("desktop-"))
        self.assertLessEqual(len(value),96)

if __name__=="__main__":
    unittest.main()
