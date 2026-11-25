"""Recreate the exact previously accepted offline catalog package, not a new runtime."""
import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile

SOURCE="70a6fa8608c52b7b832e6c46704b0663bf4c2c7f"
ZIP_SHA="3037a23330f0049ed7457d11103212c2b338c5fcb03b4b77cfef25aec4711fd4"
MANIFEST_SHA="f9f8d38e520afa9871e78cd93d5e3a31e17ff4d3f39a25be2ffebcf1f9056629"
FILES={"connectors/registry.py":"b6b735f04ca1cc2512e00a000c43b9862fa1ceb0f7d32342ecc03105d5364e72",
"console/persistent_store.py":"6fbaa6bf35673aaaa99c7dfe7fccac033869997545bf084ffea69f4ee2dfa0e1",
"gateway/catalog_audit.py":"49aa0b34b3aea863a8777f19a0bbb4b61e4d2364f9978634e2e723ac796f4991",
"gateway/catalog_read.py":"f17a4e53f54aa2c16ef40e08a56a72e27b6c821a29a938d55e478274ac336322",
"gateway/service.py":"72034948a8f15f28d62855a778fd53f3741acc58595b72418163ebce67717185",
"registry/canonical_177.json":"1c566602c5ecc7df815c7653d77f8dad65b5e12eca8017d060b5764e7d488b03",
"registry/canonical_loader.py":"af4ec6181bace7c95d93c71224055a832ccc70b768cd72b64991856733e0088c",
"tests/test_catalog_audit.py":"b6ffa711b76d5c391ad5eca4d5e97a887c4b0bf70e634dfab8f36d933e5b320d",
"tests/test_catalog_read.py":"8bd84d90bc96a84c57c8bb965eef34bd94f1fe57ea1be23937316512d0b73610"}
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":")).encode()
def build(out):
    contents={}
    for name,digest in FILES.items():
        path="cerebro-os/"+("governance/cp189_tests/"+name.split("/")[-1] if name.startswith("tests/") else name)
        raw=subprocess.check_output(["git","show",SOURCE+":"+path])
        if sha(raw)!=digest:raise ValueError("SOURCE_DRIFT:"+name)
        contents[name]=raw
    manifest={"capability":"FACT.CATALOG.READ","company_id":"fenix","deployment_authorized":False,
        "engine_id":"FACT-001","environment":"PREPROD","files":FILES,
        "historical_restore_performed":False,"runtime_identity_verified":False,
        "schema":"cerebro.catalog.rebuild.v1","source_commit":SOURCE,"version":"1.2.0"}
    contents["manifest.json"]=canonical(manifest)
    if sha(contents["manifest.json"])!=MANIFEST_SHA:raise ValueError("MANIFEST_DRIFT")
    with zipfile.ZipFile(out,"w") as z:
        for name,raw in sorted(contents.items()):
            i=zipfile.ZipInfo(name,(2026,11,25,0,0,0))
            i.create_system=3;i.external_attr=2175008768
            z.writestr(i,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    observed=sha(pathlib.Path(out).read_bytes())
    if observed!=ZIP_SHA:raise ValueError("EXACT_ZIP_DRIFT:"+observed)
    print("EXACT_CATALOG_PACKAGE_VERIFIED",observed)
if __name__=="__main__":build(sys.argv[1])
