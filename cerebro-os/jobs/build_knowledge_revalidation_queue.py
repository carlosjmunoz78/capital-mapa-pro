from __future__ import annotations
import json, os
from pathlib import Path

PRIORITY={"SUPERSEDED_BY_NEWER_EVIDENCE":100,"CONTRADICTORY_EVIDENCE":90,"PROTECTED_KIND_REQUIRES_HUMAN_OR_POLICY_REVIEW":85,"TTL_EXPIRED":60,"SOURCE_UNAVAILABLE":50}

def run()->list[Path]:
    src=Path(os.environ.get("CEREBRO_OBSOLESCENCE_ROOT",".cerebro-runtime/obsolescence"))
    out=Path(os.environ.get("CEREBRO_REVALIDATION_ROOT",".cerebro-runtime/revalidation"))
    out.mkdir(parents=True,exist_ok=True); written=[]
    for path in sorted(src.glob("*.json")):
        p=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(p,dict): raise ValueError("obsolescence payload must be object")
        company_id=str(p.get("company_id","")).strip()
        if not company_id: raise ValueError("company_id required")
        items=[]
        for d in p.get("decisions") or []:
            if str(d.get("company_id",""))!=company_id: raise ValueError("cross-company decision denied")
            if not bool(d.get("review_required",False)): continue
            reasons=list(d.get("reasons") or [])
            priority=max([PRIORITY.get(r,10) for r in reasons] or [10])
            items.append({
                "company_id":company_id,
                "knowledge_id":str(d.get("knowledge_id","")),
                "kind":str(d.get("kind","KNOWLEDGE")),
                "priority":priority,
                "reasons":reasons,
                "required_evidence":["source_uri","observed_at","evidence_hash","confidence","validated_by"],
                "allowed_actions":["REVALIDATE","MARK_SUPERSEDED","KEEP_ACTIVE","RETAIN_REFERENCE_ONLY"],
                "delete_allowed":False,
                "external_mutation_allowed":False,
                "human_review_required":bool(d.get("human_review_required",False))
            })
        items.sort(key=lambda x:(-x["priority"],x["knowledge_id"]))
        target=out/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"knowledge_revalidation_queue",
            "company_id":company_id,
            "status":"READY" if items else "EMPTY",
            "delete_allowed":False,
            "external_mutation_allowed":False,
            "items":items
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
