"""Clean source-only build of the first minimum-core capability; never deploy."""
import hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
LOCK=json.loads((BASE/"scope.json").read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def build(dest):
    files={}
    for p,expected in LOCK["files"].items():
        raw=subprocess.check_output(["git","show",LOCK["source_commit"]+":cerebro-os/"+p])
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==expected,p
        files[p]=raw
    files["manifest.json"]=json.dumps({"schema":"cerebro.minimum.build.v1","source":LOCK["source_commit"],"scope":LOCK["candidate_scope"],"production_authorized":False,"live_ingress":False,"files":{p:sha(b) for p,b in files.items()}},sort_keys=True,separators=(",",":")).encode()
    with zipfile.ZipFile(dest,"x") as z:
        for p,b in sorted(files.items()):
            i=zipfile.ZipInfo(p,(2026,11,27,0,0,0));i.create_system=3;i.external_attr=0o100644<<16
            z.writestr(i,b,compress_type=zipfile.ZIP_STORED)
def test_archive(archive):
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist())==set(LOCK["files"])|{"manifest.json"}
            m=json.loads(z.read("manifest.json"))
            assert m["production_authorized"] is False and m["live_ingress"] is False
            assert all(sha(z.read(p))==h for p,h in m["files"].items())
            z.extractall(root)
        env={k:v for k,v in os.environ.items() if k not in ("PYTHONPATH","PYTHONHOME")}
        subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","governance/cp189_tests","-p","test_catalog_*.py","-v"],cwd=root,env=env,check=True)
        smoke="""from pathlib import Path
from tempfile import TemporaryDirectory
from gateway.service import GatewayRequest
from gateway import catalog_read as c
from gateway.catalog_audit import read_with_audit
from gateway.catalog_policy import offline_policy_callback
from governance.policy import PolicyRequest
from console.persistent_store import ConsoleStore
with TemporaryDirectory() as t:
    store=ConsoleStore(Path(t)/'new.sqlite')
    req=GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION)
    cb=offline_policy_callback(selected_company_id=c.COMPANY,facts=PolicyRequest(c.COMPANY,c.COMPANY,c.ENV,c.CAPABILITY))
    kw=dict(store=store,request_id='fixture:minimum:001',user_id='fixture:local-build',now_epoch=100,policy_check=cb)
    result=read_with_audit(req,**kw)
    assert result['count']==177 and result['deployment_authorized'] is False
    assert read_with_audit(req,**kw)==result
    assert ConsoleStore(store.path).counts()=={'audit':1,'history':1}
    assert store.audit_by_company('other')==()
    print('MINIMUM_CORE_OFFLINE_COMPOSITION_OK: 177 definitions; one persistent audit and history; no production authorization')
"""
        subprocess.run([sys.executable,"-B","-c",smoke],cwd=root,env=env,check=True)
if __name__=="__main__":
    dest=Path(sys.argv[1]).resolve()
    build(dest)
    with tempfile.TemporaryDirectory() as t:
        second=Path(t)/"second.zip";build(second)
        assert dest.read_bytes()==second.read_bytes()
    test_archive(dest)
    print("CLEAN_REBUILD_OK",sha(dest.read_bytes()))
