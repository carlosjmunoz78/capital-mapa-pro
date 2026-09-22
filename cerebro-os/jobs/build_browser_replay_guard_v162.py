from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WIN=ROOT/"identity"/"windows"
EXT=ROOT/"identity"/"chrome_extension_v1_6_2"
REC=WIN/"recovery_v1_6_2"
SHELL=("INSTALL_AND_VERIFY.bat","ROLLBACK.bat","README.txt","Install-CerebroBrowserReplayGuardV162.ps1")
PAYLOAD={
 "CerebroBrowserBridgeService.ps1":WIN/"CerebroBrowserBridgeService.ps1",
 "chrome_extension_v1_4_1/manifest.json":EXT/"manifest.json",
 "chrome_extension_v1_4_1/service_worker.js":EXT/"service_worker.js",
}
def build(output:Path)->dict:
 output.parent.mkdir(parents=True,exist_ok=True)
 hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in PAYLOAD.items()}
 with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as z:
  for name in SHELL:z.write(REC/name,name)
  for name,path in PAYLOAD.items():z.write(path,"payload/"+name)
  z.writestr("payload-sha256.json",json.dumps(hashes,indent=2)+"\n")
 return {"package_version":"1.6.2","service_version":"1.4.1","artifact":str(output),
 "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"files":hashes,
 "prod_enabled":False,"external_mutation_allowed":False,"credentials_included":False}
if __name__=="__main__":
 destination=ROOT.parent/".cerebro-runtime"/"packages"/"CEREBRO_BROWSER_REPLAY_GUARD_V1_6_2.zip"
 print(json.dumps(build(destination),indent=2))
