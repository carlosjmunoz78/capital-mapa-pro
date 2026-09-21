import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from jobs.build_browser_bridge_windows_package import build_package

class BrowserBridgeAcceptanceV141Tests(unittest.TestCase):
    def test_verifier_is_fail_closed_and_secret_free(self):
        script=(ROOT/"identity"/"windows"/"Verify-CerebroBrowserBridge.ps1").read_text(encoding="utf-8")
        self.assertIn('service_version = "1.4.1"', script.lower())
        self.assertIn('"LAB"',script)
        self.assertIn('"PREPROD_DEVICE_ENROLLMENT"',script)
        self.assertIn('"REMOTE_LAB_ROUNDTRIP"',script)
        self.assertIn('raw_secret_exposed',script)
        self.assertIn('prod_activation_allowed = $false',script)
        self.assertIn('external_mutation_allowed = $false',script)

    def test_package_build_omits_pairing_secret_and_prod(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"bridge.zip"
            evidence=build_package(target)
            self.assertFalse(evidence["pairing_secret_included"])
            self.assertFalse(evidence["prod_enabled"])
            self.assertFalse(evidence["external_mutation_allowed"])
            with zipfile.ZipFile(target) as zf:
                names=set(zf.namelist())
                self.assertIn("START_CEREBRO_BROWSER_BRIDGE.bat",names)
                self.assertIn("VERIFY_CEREBRO_BROWSER_BRIDGE.bat",names)
                self.assertIn("chrome_extension_v1_4_1/manifest.json",names)
                self.assertIn("BUILD_EVIDENCE.json",names)
                self.assertNotIn("PAIRING_ONCE.txt",names)
                manifest=json.loads(zf.read("package_manifest_v1_4_1.json"))
                self.assertFalse(manifest["prod_enabled"])
                self.assertTrue(manifest["pairing_file"]["required_for_first_cloud_enrollment"])

if __name__=="__main__":
    unittest.main()
