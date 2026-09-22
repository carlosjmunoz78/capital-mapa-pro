from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
RECOVERY = WIN / "recovery_v1_4_2"
PAYLOAD = (
    "CerebroBrowserTransport.ps1",
    "Start-CerebroBrowserTransport.ps1",
    "Start-CerebroBrowserBridge.ps1",
    "package_manifest_v1_4_1.json",
)
SHELL = (
    "INSTALL_AND_VERIFY.bat",
    "Install-CerebroBrowserTransportRecovery.ps1",
    "ROLLBACK.bat",
    "README.txt",
)


def build(output: Path) -> dict:
    hashes = {name: hashlib.sha256((WIN / name).read_bytes()).hexdigest() for name in PAYLOAD}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        for name in SHELL:
            package.write(RECOVERY / name, name)
        for name in PAYLOAD:
            package.write(WIN / name, f"payload/{name}")
        package.writestr("payload-sha256.json", json.dumps(hashes, indent=2) + "\n")
    return {"output": str(output), "files": hashes, "prod_enabled": False, "pairing_included": False}


if __name__ == "__main__":
    output = ROOT.parent / ".cerebro-runtime" / "packages" / "CEREBRO_BROWSER_BRIDGE_TRANSPORT_RECOVERY_V1_4_2.zip"
    print(json.dumps(build(output), indent=2))
