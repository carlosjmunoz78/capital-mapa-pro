"""Reproducible, self-contained integration acceptance bundle.
Production is the target, NOT the execution environment of this artifact.
No network, admission, credential issuance or deployment.
"""
import hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,reason):
    if not ok:raise RuntimeError(reason)
def build(dest):
    contract=json.loads((BASE/"production_target.json").read_text())
    require(contract["target"]==dict(company_id="fenix",engine_id="FACT-001",
        capability="FACT.CATALOG.READ",environment="PROD",version="1.2.0"),"TARGET_SCOPE")
    require(contract["acceptance_environment"]=="PREPROD" and
        contract["deployment_authorized"] is False and contract["live_ingress"] is False,
        "BOUNDARY")
    files={}
    for p,lock in sorted(contract["pinned_files"].items()):
        require(not Path(p).is_absolute() and ".." not in Path(p).parts,"PATH_DENIED")
        raw=subprocess.check_output(["git","show",lock["commit"]+":cerebro-os/"+p])
        require(hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==lock["blob"],"SOURCE_DRIFT:"+p)
        files[p]=raw
    for name in ("production_target.json","verify_execution.py","test_verify_execution.py"):
        files["core/minimum/"+name]=(BASE/name).read_bytes()
    files["manifest.json"]=json.dumps({"schema":"cerebro.minimum.integration.v1",
        "target":contract["target"],"execution_environment":"PREPROD",
        "deployment_authorized":False,"live_ingress":False,"files":{p:sha(b) for p,b in files.items()}},
        sort_keys=True,separators=(",",":")).encode()
    with zipfile.ZipFile(dest,"x") as z:
        for p,b in sorted(files.items()):
            i=zipfile.ZipInfo(p,(2026,11,27,0,0,0));i.create_system=3;i.external_attr=0o100644<<16
            z.writestr(i,b,compress_type=zipfile.ZIP_STORED)
def acceptance(dest):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(dest) as z:
            m=json.loads(z.read("manifest.json"))
            require(m["execution_environment"]=="PREPROD" and m["deployment_authorized"] is False,"BOUNDARY")
            require(set(z.namelist())==set(m["files"])|{"manifest.json"},"ARCHIVE_SET")
            for p,h in m["files"].items():
                require(sha(z.read(p))==h,"ARCHIVE_DRIFT:"+p)
            z.extractall(root)
        env={k:v for k,v in os.environ.items() if k not in ("PYTHONPATH","PYTHONHOME")}
        for folder,pattern in (("governance/cp189_tests","test_catalog_*.py"),("core/minimum","test_*execution.py"),("core/minimum","test_execute_catalog.py")):
            subprocess.run([sys.executable,"-B","-m","unittest","discover","-s",folder,"-p",pattern,"-v"],cwd=root,env=env,check=True)
if __name__=="__main__":
    dest=Path(sys.argv[1]).resolve()
    build(dest)
    with tempfile.TemporaryDirectory() as tmp:
        other=Path(tmp)/"rebuild.zip";build(other)
        require(dest.read_bytes()==other.read_bytes(),"REBUILD_MISMATCH")
    acceptance(dest)
    print("INTEGRATION_PACKAGE_VERIFIED_PREPROD_ONLY",sha(dest.read_bytes()))
