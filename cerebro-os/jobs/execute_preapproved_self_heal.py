from __future__ import annotations

import json
import os
from pathlib import Path

def _rebuild_rag(company_id:str)->dict:
    from jobs.permissioned_rag_cache import build_index
    written=build_index()
    root=Path(os.environ.get("CEREBRO_RAG_INDEX_ROOT",".cerebro-runtime/rag-index"))
    target=root/f"{company_id}.json"
    return {"success":target.exists(),"evidence_ref":str(target),"written":[str(p) for p in written]}

def _rebuild_twin(company_id:str)->dict:
    from jobs.build_digital_twin_snapshot import run as twin_run
    written=twin_run()
    root=Path(os.environ.get("CEREBRO_DIGITAL_TWIN_ROOT",".cerebro-runtime/digital-twin"))
    target=root/f"{company_id}.snapshot.json"
    return {"success":target.exists(),"evidence_ref":str(target),"written":[str(p) for p in written]}

PLAYBOOKS={
    "REBUILD_RAG_INDEX":_rebuild_rag,
    "REBUILD_TWIN_SNAPSHOT":_rebuild_twin,
}

def run()->list[Path]:
    incident_root=Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))
    out_root=Path(os.environ.get("CEREBRO_SELF_HEAL_ROOT",".cerebro-runtime/self-heal"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(incident_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("incident payload must be object")
        company_id=str(payload.get("company_id","")).strip()
        environment=str(payload.get("environment","")).strip().upper()
        if not company_id: raise ValueError("company_id required")
        repairs=[]
        for incident in payload.get("incidents") or []:
            if str(incident.get("company_id",""))!=company_id:
                raise ValueError("cross-company incident denied")
            repair_id=incident.get("preapproved_repair_id")
            if not repair_id:
                repairs.append({
                    "incident_id":str(incident.get("incident_id","")),
                    "repair_id":None,
                    "status":"SKIPPED_NOT_PREAPPROVED",
                    "human_reason":incident.get("human_reason"),
                    "external_mutation_allowed":False,
                })
                continue
            if environment=="PROD":
                repairs.append({
                    "incident_id":str(incident.get("incident_id","")),
                    "repair_id":repair_id,
                    "status":"HUMAN_REQUIRED",
                    "human_reason":"HIGH_RISK",
                    "external_mutation_allowed":False,
                })
                continue
            action=PLAYBOOKS.get(str(repair_id))
            if action is None:
                repairs.append({
                    "incident_id":str(incident.get("incident_id","")),
                    "repair_id":repair_id,
                    "status":"BLOCKED_UNKNOWN_PLAYBOOK",
                    "external_mutation_allowed":False,
                })
                continue
            result=action(company_id)
            repairs.append({
                "incident_id":str(incident.get("incident_id","")),
                "repair_id":repair_id,
                "status":"FIXED" if result["success"] else "FAILED_POSTCHECK",
                "post_fix_evidence_ref":result["evidence_ref"],
                "idempotent":True,
                "rollback_required":False,
                "attempt":1,
                "max_attempts":1,
                "external_mutation_allowed":False,
            })

        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"self_heal_result",
            "company_id":company_id,
            "engine_id":"SELF-001",
            "environment":environment,
            "repairs":repairs,
            "status":"GREEN" if all(r["status"] in {"FIXED","SKIPPED_NOT_PREAPPROVED"} for r in repairs) else "ATTENTION",
            "preapproved_only":True,
            "external_mutation_allowed":False,
            "cost_eur":0.0,
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
