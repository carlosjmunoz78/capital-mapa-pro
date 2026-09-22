import json
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVICE = ROOT / "identity" / "windows" / "CerebroBrowserBridgeService.ps1"
TRANSPORT = ROOT / "identity" / "windows" / "CerebroBrowserTransport.ps1"
EXT = ROOT / "identity" / "chrome_extension_v1_5"


class BrowserMetadataPilotV15Tests(unittest.TestCase):
    def test_extension_has_only_fixed_example_com_host(self):
        manifest = json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))
        worker = (EXT / "service_worker.js").read_text(encoding="utf-8")
        self.assertEqual(manifest["version"], "1.5.0")
        self.assertEqual(manifest["permissions"], ["alarms"])
        self.assertEqual(manifest["host_permissions"],
                         ["http://127.0.0.1/*", "https://example.com/*"])
        self.assertNotIn("scripting", manifest["permissions"])
        self.assertNotIn("tabs", manifest["permissions"])
        self.assertIn('ALLOWED_URL = "https://example.com/"', worker)
        self.assertNotIn("chrome.cookies", worker)
        self.assertNotIn("chrome.scripting", worker)

    def test_transport_requires_readback_for_semantic_success(self):
        source = TRANSPORT.read_text(encoding="utf-8")
        self.assertIn('"READ_ONLY_PAGE_METADATA"', source)
        self.assertIn('"EXAMPLE_DOMAIN_METADATA_VERIFIED"', source)
        self.assertIn('"https://example.com/"', source)
        self.assertIn('"Example Domain"', source)
        self.assertIn('REMOTE_ACTION_DENIED', source)

    @unittest.skipUnless(shutil.which("powershell.exe") or shutil.which("pwsh"),
                         "PowerShell required")
    def test_local_service_exact_metadata_readback_and_redirect_denial(self):
        executable = shutil.which("powershell.exe") or shutil.which("pwsh")
        with tempfile.TemporaryDirectory(prefix="Cerebro Pilot ") as temporary:
            tmp = pathlib.Path(temporary)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            args = [executable, "-NoProfile"]
            if pathlib.Path(executable).name.lower() == "powershell.exe":
                args += ["-ExecutionPolicy", "Bypass"]
            args += ["-File", str(SERVICE), "-Port", str(port),
                     "-StatePath", str(tmp / "state.json"),
                     "-TransportKey", "ci-test-key"]
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, text=True)
            base = f"http://127.0.0.1:{port}"

            def get(route, **query):
                path = base + route
                if query:
                    path += "?" + urllib.parse.urlencode(query)
                with urllib.request.urlopen(path, timeout=3) as response:
                    return response.read().decode("utf-8")

            try:
                ready = False
                for _ in range(40):
                    if proc.poll() is not None:
                        self.fail("Bridge exited unexpectedly")
                    try:
                        ready = json.loads(get("/health"))["status"] == "GREEN"
                    except (urllib.error.URLError, ValueError):
                        pass
                    if ready:
                        break
                    time.sleep(0.2)
                self.assertTrue(ready, "local service did not become ready")

                get("/pair", company_id="fenix", profile_id="Default",
                    browser_family="CHROME", environment="LAB", version="v0")
                ext_id = "c" * 32
                ping = json.loads(get("/extension/ping", extension_id=ext_id,
                                      extension_version="1.5.0"))
                self.assertEqual(ping["status"], "GREEN")

                def run_case(command_id, observed_url, title, complete, expected):
                    enqueued = json.loads(get(
                        "/cloud/enqueue", transport_key="ci-test-key",
                        command_id=command_id, action="READ_ONLY_PAGE_METADATA"))
                    self.assertEqual(enqueued["status"], "GREEN")
                    dispatched = json.loads(get("/extension/command", extension_id=ext_id))
                    self.assertEqual(dispatched["target_url"], "https://example.com/")
                    self.assertEqual(dispatched["action"], "READ_ONLY_PAGE_METADATA")
                    get("/extension/result", extension_id=ext_id,
                        command_id=command_id, result="COMPLETED",
                        observed_url=observed_url, observed_title=title,
                        page_load_complete=str(complete).lower())
                    state = json.loads(get("/health"))
                    self.assertEqual(state["lab_command_status"], expected)
                    return state

                good = run_case("metadata-ci-1", "https://example.com/",
                                "Example Domain", True, "COMPLETED")
                self.assertEqual(good["lab_command_evidence"],
                                 "EXAMPLE_DOMAIN_METADATA_VERIFIED")
                self.assertTrue(good["lab_command_page_load_complete"])

                bad = run_case("metadata-ci-2", "https://another.example/",
                               "Example Domain", True, "FAILED")
                self.assertEqual(bad["lab_command_evidence"], "PAGE_READBACK_FAILED")
                self.assertEqual(bad["lab_command_observed_url"], "")

                get("/extension/ping", extension_id=ext_id, extension_version="1.4.1")
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    get("/cloud/enqueue", transport_key="ci-test-key",
                        command_id="metadata-ci-3",
                        action="READ_ONLY_PAGE_METADATA")
                self.assertEqual(denied.exception.code, 400)
            finally:
                proc.terminate()
                try:
                    proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
