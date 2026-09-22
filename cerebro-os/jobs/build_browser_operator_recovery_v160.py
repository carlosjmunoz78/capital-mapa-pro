from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
EXT = ROOT / "identity" / "chrome_extension_v1_6"
RECOVERY = WIN / "recovery_v1_6"
SHELL = ("INSTALL_AND_VERIFY.bat", "Install-CerebroBrowserOperatorRecovery.ps1", "ROLLBACK.bat", "README.txt")
PAYLOAD = {
    "CerebroBrowserBridgeService.ps1": WIN / "CerebroBrowserBridgeService.ps1",
    "CerebroBrowserTransport.ps1": WIN / "CerebroBrowserTransport.ps1",
    "chrome_extension_v1_4_1/manifest.json": EXT / "manifest.json",
    "chrome_extension_v1_4_1/service_worker.js": EXT / "service_worker.js",
}
def build(output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    hashes = {name: hashlib.sha256(source.read_bytes()).hexdigest() for name, source in PAYLOAD.items()}
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in SHELL:
            archive.write(RECOVERY / name, name)
        for name, source in PAYLOAD.items():
            archive.write(source, "payload/" + name)
        archive.writestr("payload-sha256.json", json.dumps(hashes, indent=2) + "\n")
    return {"package_version": "1.6.0", "service_version": "1.4.1",
            "artifact": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": hashes, "prod_enabled": False, "external_mutation_allowed": False,
            "credentials_included": False}
if __name__ == "__main__":
    dest = ROOT.parent / ".cerebro-runtime" / "packages" / "CEREBRO_BROWSER_OPERATOR_RECOVERY_V1_6_0.zip"
    print(json.dumps(build(dest), indent=2))
