from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="AUTBOOT-001"

def bootstrap_automations(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    workflows=payload.get("workflow_candidates") or []
    existing=payload.get("existing_automation_refs") or []
    if not isinstance(workflows,list) or not isinstance(existing,list): raise ValueError("workflow_candidates and existing_automation_refs must be lists")
    candidates=[]
    for i,item in enumerate(workflows,1):
        if not isinstance(item,dict): raise ValueError("workflow candidate must be object")
        trigger=str(item.get("trigger","")).strip(); action=str(item.get("action","")).strip()
        if not trigger or not action: raise ValueError("workflow candidate requires trigger and action")
        candidates.append({"automation_id":str(item.get("automation_id") or f"AUT-CAND-{i:03d}"),"trigger":trigger,"action":action,"external_side_effect":bool(item.get("external_side_effect",False)),"promotion_status":"PREPROD_CANDIDATE"})
    canonical=json.dumps({"company_id":company_id,"existing":sorted(map(str,existing)),"candidates":candidates},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"automation_bootstrap_plan","company_id":company_id,"engine_id":ENGINE_ID,"environment":"PREPROD","version":str(payload.get("version","1.0.0")),
      "status":"GREEN" if candidates else "WAITING","existing_automation_refs":sorted(map(str,existing)),"workflow_candidates":candidates,
      "prod_execution_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
      "required_gates":["POL-001","QA-001","REG-001","OBSERV-001","TENANT-001"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_AUTBOOT_REQUEST_ROOT",".cerebro-runtime/autboot-requests"))
    out=Path(os.environ.get("CEREBRO_AUTBOOT_RESULT_ROOT",".cerebro-runtime/autboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_automations(json.loads(path.read_text(encoding="utf-8"))); target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
