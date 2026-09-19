from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

PROTECTED_KINDS={"POLICY","LEGAL_RULE","PERMISSION","SECURITY_CONTROL"}

def _canonical_hash(source_uri:str, observed_at:str, validated_by:str, content_hash:str, confidence:float)->str:
    raw="|".join([source_uri,observed_at,validated_by,content_hash,f"{confidence:.6f}"])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def run()->list[Path]:
    queue_root=Path(os.environ.get("CEREBRO_REVALIDATION_ROOT",".cerebro-runtime/revalidation"))
    evidence_root=Path(os.environ.get("CEREBRO_REVALIDATION_EVIDENCE_ROOT",".cerebro-runtime/revalidation-evidence"))
    out_root=Path(os.environ.get("CEREBRO_PROVENANCE_VALIDATION_ROOT",".cerebro-runtime/provenance-validation"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for qpath in sorted(queue_root.glob("*.json")):
        queue=json.loads(qpath.read_text(encoding="utf-8"))
        if not isinstance(queue,dict): raise ValueError("revalidation queue must be object")
        company_id=str(queue.get("company_id","")).strip()
        if not company_id: raise ValueError("company_id required")
        results=[]
        for item in queue.get("items") or []:
            if str(item.get("company_id",""))!=company_id: raise ValueError("cross-company queue item denied")
            knowledge_id=str(item.get("knowledge_id","")).strip()
            kind=str(item.get("kind","KNOWLEDGE")).strip().upper()
            ep=evidence_root/company_id/f"{knowledge_id}.json"
            status="WAITING"; reasons=["EVIDENCE_MISSING"]; evidence_ref=""
            payload={}
            if ep.exists():
                payload=json.loads(ep.read_text(encoding="utf-8"))
                if not isinstance(payload,dict): raise ValueError("revalidation evidence must be object")
                if str(payload.get("company_id",""))!=company_id: raise ValueError("cross-company evidence denied")
                if str(payload.get("knowledge_id",""))!=knowledge_id: raise ValueError("knowledge identity mismatch")
                source_uri=str(payload.get("source_uri","")).strip()
                observed_at=str(payload.get("observed_at","")).strip()
                validated_by=str(payload.get("validated_by","")).strip()
                content_hash=str(payload.get("content_hash","")).strip()
                confidence=float(payload.get("confidence",0.0))
                evidence_hash=str(payload.get("evidence_hash","")).strip()
                expected=_canonical_hash(source_uri,observed_at,validated_by,content_hash,confidence) if all((source_uri,observed_at,validated_by,content_hash)) else ""
                valid=bool(expected) and evidence_hash==expected and 0<=confidence<=1
                if not valid:
                    status="BLOCKED"; reasons=["PROVENANCE_INVALID"]
                elif kind in PROTECTED_KINDS or bool(item.get("human_review_required",False)):
                    status="HUMAN_REQUIRED"; reasons=["POLICY_CONFLICT" if kind=="POLICY" else "LEGAL_REQUIRED" if kind=="LEGAL_RULE" else "HIGH_RISK"]
                elif confidence < 0.80:
                    status="HUMAN_REQUIRED"; reasons=["LOW_CONFIDENCE"]
                else:
                    status="GREEN"; reasons=[]
                evidence_ref=f"file://{ep}"
            results.append({
                "company_id":company_id,
                "knowledge_id":knowledge_id,
                "kind":kind,
                "engine_id":"PRV-001",
                "status":status,
                "reasons":reasons,
                "evidence_ref":evidence_ref,
                "source_uri":str(payload.get("source_uri","")),
                "observed_at":str(payload.get("observed_at","")),
                "validated_by":str(payload.get("validated_by","")),
                "content_hash":str(payload.get("content_hash","")),
                "confidence":float(payload.get("confidence",0.0)) if payload else 0.0,
                "evidence_hash":str(payload.get("evidence_hash","")),
                "external_mutation_allowed":False,
                "delete_allowed":False,
                "history_preserved":True
            })
        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"provenance_revalidation_results",
            "company_id":company_id,
            "engine_id":"PRV-001",
            "status":"GREEN" if results and all(r["status"]=="GREEN" for r in results) else "ATTENTION",
            "results":results,
            "external_mutation_allowed":False,
            "delete_allowed":False
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
