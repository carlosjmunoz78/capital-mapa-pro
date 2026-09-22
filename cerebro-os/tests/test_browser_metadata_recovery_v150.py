import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "jobs"))
from build_browser_metadata_recovery_v150 import build


class BrowserMetadataRecoveryV150Tests(unittest.TestCase):
    def test_builder_is_scoped_and_contains_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "pilot.zip"
            evidence = build(out)
            self.assertEqual(evidence["package_version"], "1.5.0")
            self.assertFalse(evidence["prod_enabled"])
            self.assertFalse(evidence["credentials_included"])
            self.assertFalse(evidence["external_mutation_allowed"])
            with zipfile.ZipFile(out) as z:
                names = set(z.namelist())
                self.assertIn("INSTALL_AND_VERIFY.bat", names)
                self.assertIn("ROLLBACK.bat", names)
                self.assertIn("payload/CerebroBrowserBridgeService.ps1", names)
                self.assertIn("payload/CerebroBrowserTransport.ps1", names)
                self.assertIn("payload/chrome_extension_v1_4_1/manifest.json", names)
                self.assertIn("payload/chrome_extension_v1_4_1/service_worker.js", names)
                hashes = json.loads(z.read("payload-sha256.json"))
                self.assertEqual(set(hashes), set(evidence["files"]))

    def test_installer_preserves_extension_path_and_requires_physical_reload(self):
        installer = (ROOT / "identity/windows/recovery_v1_5/Install-CerebroBrowserMetadataRecovery.ps1").read_text()
        self.assertIn("chrome_extension_v1_4_1", installer)
        self.assertIn("recovery-backup-v150-", installer)
        self.assertIn("PAYLOAD_HASH_MISMATCH", installer)
        self.assertIn("RELOAD_EXISTING_CHROME_EXTENSION_V150_AND_REMOTE_LAB_ROUNDTRIP", installer)
        self.assertIn("prod_enabled=$false", installer)
        self.assertNotIn("token=", installer.lower())
        self.assertNotIn("password=", installer.lower())

    def test_payload_is_fixed_host_metadata_only(self):
        worker = (ROOT / "identity/chrome_extension_v1_5/service_worker.js").read_text()
        manifest = (ROOT / "identity/chrome_extension_v1_5/manifest.json").read_text()
        transport = (ROOT / "identity/windows/CerebroBrowserTransport.ps1").read_text()
        self.assertIn('const ALLOWED_URL = "https://example.com/";', worker)
        self.assertIn("READ_ONLY_PAGE_METADATA", worker)
        self.assertIn("Example Domain", worker)
        manifest_data = json.loads(manifest)
        self.assertNotIn("cookies", manifest_data["permissions"])
        self.assertNotIn("<all_urls>", manifest_data["host_permissions"])
        self.assertEqual(set(manifest_data["host_permissions"]), {"http://127.0.0.1/*", "https://example.com/*"})
        self.assertIn("READ_ONLY_PAGE_METADATA", transport)
        self.assertIn("EXAMPLE_DOMAIN_METADATA_VERIFIED", transport)


if __name__ == "__main__":
    unittest.main()
