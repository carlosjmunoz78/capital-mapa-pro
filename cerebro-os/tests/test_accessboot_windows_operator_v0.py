"""ACCESSBOOT cross-version + reversible package regression contracts."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
PKG = WIN / "accessboot_v0"
EXT = ROOT / "identity" / "chrome_extension_v1_7_0"


def read(path):
    return path.read_text(encoding="utf-8")


class AccessbootContract(unittest.TestCase):
    def test_cross_version_launchers_bridge_transport_extension(self):
        launcher = read(WIN / "Start-CerebroBrowserBridge.ps1")
        transport_launcher = read(WIN / "Start-CerebroBrowserTransport.ps1")
        bridge = read(PKG / "payload/CerebroBrowserBridgeService.ps1")
        transport = read(PKG / "payload/CerebroBrowserTransport.ps1")
        worker = read(PKG / "payload/chrome_extension_v1_4_1/service_worker.js")
        manifest = json.loads(read(PKG / "payload/chrome_extension_v1_4_1/manifest.json"))
        self.assertEqual(manifest["version"], "1.7.0")
        self.assertIn('$ExpectedServiceVersion = "1.4.1"', launcher)
        self.assertIn("$TransportKeyPath = Join-Path $RuntimeDir", launcher)
        self.assertIn("transport-local-key-1.4.1.txt", launcher)
        self.assertIn("$h.service_version -eq '1.4.1'", transport_launcher)
        self.assertIn("transport-1.4.1.json", transport_launcher)
        self.assertIn('$ServiceVersion = "1.4.1"', bridge)
        self.assertIn('$TransportVersion = "1.4.1"', transport)
        self.assertIn('EXPECTED_SERVICE_VERSION = "1.4.1"', worker)
        self.assertIn('EXTENSION_VERSION = "1.7.0"', worker)
        self.assertIn('"1.7.0"', bridge)
        self.assertIn("cerebro_local_test_receipt_ledger_v162", worker)
        self.assertIn("cerebro_accessboot_browser_ledger_v170", worker)
        self.assertEqual(worker, read(EXT / "service_worker.js"))
        self.assertEqual(manifest, json.loads(read(EXT / "manifest.json")))
        self.assertEqual(bridge, read(PKG / "CerebroBrowserBridgeService.ps1"))
        self.assertEqual(transport, read(PKG / "CerebroBrowserTransport.ps1"))

    def test_filesystem_scoped_and_resumable(self):
        transport = read(PKG / "payload/CerebroBrowserTransport.ps1")
        for term in (
            'FS_CREATE_DIRECTORY', 'GetFolderPath("MyDocuments")',
            'FS_PATH_DENIED', 'FS_SCOPE_DENIED', 'DIRECTORY_EXISTS_VERIFIED',
            'Assert-NoReparsePath $root $relative', '[IO.FileAttributes]::ReparsePoint',
            'DIRECT_LEDGER_INVALID', 'COMMAND_ID_PAYLOAD_CONFLICT',
            'phase="CLAIMED"', 'phase="TERMINAL"', 'FS_READBACK_FAILED'
        ):
            self.assertIn(term, transport)
        self.assertNotIn("Invoke-Expression", transport)
        self.assertNotIn("cmd.exe /c", transport)

    def test_browser_guard_and_replay(self):
        bridge = read(PKG / "payload/CerebroBrowserBridgeService.ps1")
        transport = read(PKG / "payload/CerebroBrowserTransport.ps1")
        worker = read(PKG / "payload/chrome_extension_v1_4_1/service_worker.js")
        manifest = json.loads(read(PKG / "payload/chrome_extension_v1_4_1/manifest.json"))
        self.assertIn("BROWSER_URL_SCOPE_DENIED", bridge)
        self.assertIn("BROWSER_URL_OPENED_VERIFIED", transport)
        self.assertIn("Test-BrowserReceipt", transport)
        self.assertIn("https", bridge)
        self.assertIn("192\\.168", bridge)
        self.assertIn("u.protocol!==\"https:\"", worker)
        self.assertIn('chrome.tabs.create({url:target,active:true})', worker)
        self.assertIn('phase:"CLAIMED"', worker)
        self.assertIn('phase:"TERMINAL"', worker)
        self.assertIn("CEREBRO_BROWSER_COMMAND_AMBIGUOUS_NO_REPLAY", worker)
        self.assertIn("consent.youtube.com", worker)
        self.assertIn("consent.youtube.com", transport)
        self.assertIn("consent.youtube.com", bridge)
        self.assertIn("tabs", manifest["permissions"])

    def test_installer_hash_backup_rollback_and_non_interference(self):
        installer = read(PKG / "Install-CerebroAccessbootV0.ps1")
        for term in (
            'prod_enabled=$false', 'BRIDGE_NOT_SAFE', 'kill_switch_enabled',
            'PACKAGE_HASH_MISMATCH', 'CROSS_VERSION_CONTRACT_MISMATCH',
            'Snapshot', 'Assert-EqualHashes', 'Stop-ScopedProcesses',
            'Get-FileHash', 'recovery-v1.6.2.json',
            'transport-1.4.1.json', 'PREVIOUS_SNAPSHOT_EXISTS_USE_ROLLBACK_OR_REVIEW',
            'ROLLED_BACK', 'POST_START_HEALTH_NOT_VERIFIED'
        ):
            self.assertIn(term.lower(), installer.lower())
        self.assertNotIn("Stop-Cerebro", installer)
        self.assertNotIn('Remove-Item -LiteralPath $Runtime', installer)

    def test_static_package_does_not_contain_secrets(self):
        for path in PKG.glob("**/*"):
            if not path.is_file() or path.suffix not in (".ps1", ".json", ".js", ".txt", ".cmd"):
                continue
            if path.name == "manifest-sha256.json":
                continue
            self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY=", read(path))


if __name__ == "__main__":
    unittest.main()
