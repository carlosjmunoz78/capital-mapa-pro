import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
WIN=ROOT/"identity"/"windows"

class BrowserBridgeWindowsNativePackageV1Tests(unittest.TestCase):
    def test_native_package_has_no_python_runtime_dependency(self):
        launcher=(WIN/"Start-CerebroBrowserBridge.ps1").read_text(encoding="utf-8")
        bat=(WIN/"START_CEREBRO_BROWSER_BRIDGE.bat").read_text(encoding="utf-8")
        self.assertNotIn("python",launcher.lower())
        self.assertNotIn("py -3",launcher.lower())
        self.assertNotIn("python",bat.lower())
        self.assertIn("CerebroBrowserBridgeService.ps1",launcher)

    def test_launcher_validates_service_identity_and_port_collision(self):
        launcher=(WIN/"Start-CerebroBrowserBridge.ps1").read_text(encoding="utf-8")
        self.assertIn("CEREBRO Browser Bridge",launcher)
        self.assertIn("8766..8785",launcher)
        self.assertIn("Test-PortFree",launcher)
        self.assertIn("/health",launcher)
        self.assertIn("launcher.log",launcher)
        self.assertIn('$ExpectedServiceVersion = "1.3.0"',launcher)
        self.assertIn('$json.service_version -eq $ExpectedServiceVersion',launcher)

    def test_service_is_loopback_and_fail_closed_for_prod(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn("[System.Net.IPAddress]::Loopback",service)
        self.assertIn('$ServiceVersion = "1.3.0"',service)
        self.assertIn('@("LAB","PREPROD")',service)
        self.assertIn('cloud_transport_status = "NOT_CONFIGURED"',service)
        self.assertNotIn("0.0.0.0",service)

    def test_form_collects_no_credentials(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn('form method="get"',service)
        self.assertIn('Empresa',service)
        self.assertIn('Perfil del navegador',service)
        self.assertNotIn('type="password"',service.lower())

    def test_local_chrome_discovery_is_metadata_only(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn('Discover-Chrome',service)
        self.assertIn('Canonicalize-ProfileId',service)
        self.assertIn('profile_directory',service)
        self.assertIn('display_name',service)
        self.assertIn('browser_discovery_status',service)
        self.assertNotIn('Cookies',service)
        self.assertNotIn('Login Data',service)
        self.assertNotIn('Web Data',service)

    def test_extension_heartbeat_is_local_and_non_mutating(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        self.assertIn('/extension/ping',service)
        self.assertIn('EXTENSION_HEARTBEAT_ACCEPTED',service)
        self.assertIn('external_mutation_allowed = $false',service)
        self.assertIn('cloud_transport_configured = $false',service)

    def test_extension_manifest_has_no_page_access(self):
        ext=ROOT/"identity"/"chrome_extension_v1_2"
        manifest=(ext/"manifest.json").read_text(encoding="utf-8")
        worker=(ext/"service_worker.js").read_text(encoding="utf-8")
        self.assertIn('"version": "1.2.0"',manifest)
        self.assertIn('"http://127.0.0.1/*"',manifest)
        self.assertNotIn('"tabs"',manifest)
        self.assertNotIn('"scripting"',manifest)
        self.assertNotIn('"<all_urls>"',manifest)
        self.assertIn('/extension/ping',worker)

if __name__=="__main__":
    unittest.main()

    def test_lab_actuation_v13_is_local_only(self):
        service=(WIN/"CerebroBrowserBridgeService.ps1").read_text(encoding="utf-8")
        ext=ROOT/"identity"/"chrome_extension_v1_3"
        manifest=(ext/"manifest.json").read_text(encoding="utf-8")
        worker=(ext/"service_worker.js").read_text(encoding="utf-8")
        self.assertIn('/lab/queue-test',service)
        self.assertIn('/extension/command',service)
        self.assertIn('/extension/result',service)
        self.assertIn('OPEN_LOCAL_TEST_PAGE',service)
        self.assertIn('IDEMPOTENT_REPLAY_SUPPRESSED',service)
        self.assertIn('"version": "1.3.0"',manifest)
        self.assertIn('"http://127.0.0.1/*"',manifest)
        self.assertNotIn('"<all_urls>"',manifest)
        self.assertNotIn('"scripting"',manifest)
        self.assertIn('chrome.tabs.create',worker)
        self.assertIn('startsWith("http://127.0.0.1:"',worker)
