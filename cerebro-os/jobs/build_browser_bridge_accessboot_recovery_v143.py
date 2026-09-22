from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
RECOVERY = WIN / "recovery_v1_4_3"
PAYLOAD = ("CerebroBrowserTransport.ps1",)
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
    return {
        "output": str(output),
        "files": hashes,
        "package_version": "1.4.3",
        "service_version": "1.4.1",
        "capability": "ACCESSBOOT_CAPABILITY_SNAPSHOT",
        "prod_enabled": False,
        "external_mutation_allowed": False,
        "pairing_included": False,
        "cost_eur": 0.0,
    }


if __name__ == "__main__":
    output = ROOT.parent / ".cerebro-runtime" / "packages" / "CEREBRO_BROWSER_BRIDGE_ACCESSBOOT_RECOVERY_V1_4_3.zip"
    print(json.dumps(build(output), indent=2))
