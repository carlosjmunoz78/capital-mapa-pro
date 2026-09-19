from __future__ import annotations
import json,os
from pathlib import Path
from identity.access_health import evaluate_access_health,access_recovery_plan

def build_snapshot(payload:dict)->dict:
    snapshot=evaluate_access_health(
        company_id=str(payload.get("company_id","")).strip(),
        environment=str(payload.get("environment","LAB")).upper(),
        version=str(payload.get("version","1.0.0")),
        accounts=list(payload.get("accounts") or []),
        sessions=list(payload.get("sessions") or []),
        credentials=list(payload.get("credentials") or []),
        connectors=list(payload.get("connectors") or []),
        bridge_heartbeats=list(payload.get("bridge_heartbeats") or []),
    )
    return {**snapshot,"recovery_plan":access_recovery_plan(snapshot),"engine_id":"ACCESS-HLT-001"}

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_ACCESS_HEALTH_REQUEST_ROOT",".cerebro-runtime/access-health-requests"))
    out=Path(os.environ.get("CEREBRO_ACCESS_HEALTH_RESULT_ROOT",".cerebro-runtime/access-health-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=build_snapshot(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
