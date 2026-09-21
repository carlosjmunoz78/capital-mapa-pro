from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN = ROOT / "identity" / "windows"
EXT = ROOT / "identity" / "chrome_extension_v1_4_1"
MANIFEST = WIN / "package_manifest_v1_4_1.json"

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def build_package(output_path: Path) -> dict:
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required = [WIN / name for name in spec["required_files"]]
    ext_files = sorted(p for p in EXT.rglob("*") if p.is_file())
    files = required + [MANIFEST] + ext_files
    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError("missing package files: " + ", ".join(missing))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            if path.parent == WIN:
                arc = path.name
            elif path == MANIFEST:
                arc = path.name
            else:
                arc = "chrome_extension_v1_4_1/" + path.relative_to(EXT).as_posix()
            zf.write(path, arc)
            entries.append({"path": arc, "sha256": _sha256(path)})
        evidence = {
            "record_type": "cerebro_browser_bridge_package_build",
            "service_version": spec["service_version"],
            "files": entries,
            "pairing_secret_included": False,
            "prod_enabled": False,
            "external_mutation_allowed": False,
            "cost_eur": 0.0,
        }
        zf.writestr("BUILD_EVIDENCE.json", json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return evidence

if __name__ == "__main__":
    target = ROOT.parent / ".cerebro-runtime" / "packages" / "CEREBRO_BROWSER_BRIDGE_WINDOWS_V1_4_1.zip"
    print(json.dumps(build_package(target), sort_keys=True, indent=2))
