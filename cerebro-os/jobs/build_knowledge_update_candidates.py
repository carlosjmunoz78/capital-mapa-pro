from __future__ import annotations

import json
import os
from pathlib import Path

def run()->list[Path]:
    src=Path(os.environ.get("CEREBRO_PROVENANCE_VALIDATION_ROOT",".cerebro-runtime/provenance-validation"))
    out=Path(os.environ.get("CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT",".cerebro-runtime/knowledge-update-candidates"))
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(src.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("provenance result must be object")
        company_id=str(payload.get("company_id","")).strip()
        if not company_id: raise ValueError("company_id required")
        candidates=[]
        attention=[]
        for r in payload.get("results") or []:
            if str(r.get("company_id",""))!=company_id: raise ValueError("cross-company provenance result denied")
            status=str(r.get("status",""))
            if status!="GREEN":
                attention.append({
                    "knowledge_id":str(r.get("knowledge_id","")),
                    "status":status,
                    "reasons":list(r.get("reasons") or [])
                })
                continue
            candidates.append({
                "company_id":company_id,
                "engine_id":"UPD-001",
                "knowledge_id":str(r.get("knowledge_id","")),
                "kind":str(r.get("kind","KNOWLEDGE")),
                "candidate_version":"revalidated-"+str(r.get("content_hash",""))[:12],
                "provenance_id":str(r.get("provenance_id","")),
                "source_type":str(r.get("source_type","")),
                "source_uri":str(r.get("source_uri","")),
                "observed_at":str(r.get("observed_at","")),
                "validated_by":str(r.get("validated_by","")),
                "content_hash":str(r.get("content_hash","")),
                "evidence_hash":str(r.get("evidence_hash","")),
                "confidence":float(r.get("confidence",0.0)),
                "status":"CANDIDATE_ONLY",
                "append_only":True,
                "supersedes_previous":True,
                "history_preserved":True,
                "auto_apply_allowed":False,
                "production_ready":False,
                "external_mutation_allowed":False,
                "delete_allowed":False,
                "required_gates":["contract_tests","evaluation","tribunal","old_vs_new","rollback","backup_rebuild","observability"]
            })
        target=out/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"knowledge_update_candidates",
            "company_id":company_id,
            "engine_id":"UPD-001",
            "status":"CANDIDATES_READY" if candidates else "NO_SAFE_CANDIDATES",
            "candidates":candidates,
            "attention":attention,
            "auto_apply_allowed":False,
            "external_mutation_allowed":False,
            "delete_allowed":False
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
