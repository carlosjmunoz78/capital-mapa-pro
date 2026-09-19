from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ALLOWED_ITEM_TYPES={"FACT","COMMITMENT","TASK","RISK","DECISION"}
SENSITIVE_DOMAINS={"LEGAL","FISCAL","SECURITY","PAYMENT","PERMISSION","POLICY"}
CANONICAL_HUMAN_REASONS={"LEGAL_REQUIRED","SIGNATURE_REQUIRED","LOW_CONFIDENCE","HIGH_RISK","POLICY_CONFLICT","SECURITY_INCIDENT","MONEY_LIMIT","CUSTOMER_HUMAN_REQUEST"}


def _candidate_id(company_id:str, conversation_id:str, item_type:str, index:int, text:str)->str:
    raw="|".join([company_id,conversation_id,item_type,str(index),text])
    return "con-"+hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def normalize_conversation(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    conversation_id=str(payload.get("conversation_id","")).strip()
    environment=str(payload.get("environment","LAB")).strip().upper()
    version=str(payload.get("version","1.0.0")).strip()
    source_type=str(payload.get("source_type","")).strip().upper()
    source_uri=str(payload.get("source_uri","")).strip()
    observed_at=str(payload.get("observed_at","")).strip()
    if not all((company_id,conversation_id,environment,version,source_type,source_uri,observed_at)):
        raise ValueError("complete conversation scope and provenance required")

    raw_items=payload.get("items")
    if not isinstance(raw_items,list):
        raise ValueError("structured conversation items must be list")
    candidates=[]
    for idx,item in enumerate(raw_items):
        if not isinstance(item,dict):
            raise ValueError("conversation item must be object")
        item_type=str(item.get("type","")).strip().upper()
        if item_type not in ALLOWED_ITEM_TYPES:
            raise ValueError("unsupported conversation item type")
        text=str(item.get("text","")).strip()
        if not text:
            raise ValueError("conversation item text required")
        confidence=float(item.get("confidence",0.0))
        if confidence<0 or confidence>1:
            raise ValueError("confidence must be between 0 and 1")
        domain=str(item.get("domain","GENERAL")).strip().upper()
        sensitive=domain in SENSITIVE_DOMAINS
        human_reason=None
        if confidence<0.80:
            human_reason="LOW_CONFIDENCE"
        elif sensitive:
            if domain=="LEGAL":
                human_reason="LEGAL_REQUIRED"
            elif domain=="SECURITY":
                human_reason="SECURITY_INCIDENT"
            elif domain in {"POLICY","PERMISSION"}:
                human_reason="POLICY_CONFLICT"
            else:
                human_reason="HIGH_RISK"
        if human_reason and human_reason not in CANONICAL_HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")

        candidates.append({
            "candidate_id":_candidate_id(company_id,conversation_id,item_type,idx,text),
            "company_id":company_id,
            "engine_id":"CON-001",
            "environment":environment,
            "version":version,
            "conversation_id":conversation_id,
            "item_type":item_type,
            "domain":domain,
            "text":text,
            "confidence":confidence,
            "source_type":source_type,
            "source_uri":source_uri,
            "observed_at":observed_at,
            "speaker_ref":str(item.get("speaker_ref","")),
            "status":"HUMAN_REQUIRED" if human_reason else "CANDIDATE_ONLY",
            "human_reason":human_reason,
            "knowledge_write_allowed":False,
            "auto_promote_allowed":False,
            "external_mutation_allowed":False,
            "production_ready":False,
            "requires_provenance_validation":True,
            "required_gates":["PRV-001","UPD-001","evaluation","tribunal"],
        })
    return {
        "record_type":"conversation_knowledge_candidates",
        "company_id":company_id,
        "engine_id":"CON-001",
        "environment":environment,
        "version":version,
        "conversation_id":conversation_id,
        "source_type":source_type,
        "source_uri":source_uri,
        "observed_at":observed_at,
        "candidates":candidates,
        "raw_text_extraction_performed":False,
        "knowledge_write_allowed":False,
        "auto_promote_allowed":False,
        "external_mutation_allowed":False,
        "production_ready":False,
        "cost_eur":0.0,
    }


def run()->list[Path]:
    source_root=Path(os.environ.get(
        "CEREBRO_CONVERSATION_STRUCTURED_ROOT",
        ".cerebro-runtime/conversations-structured",
    ))
    out_root=Path(os.environ.get(
        "CEREBRO_CONVERSATION_KNOWLEDGE_ROOT",
        ".cerebro-runtime/conversation-knowledge",
    ))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        raw=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw,dict):
            raise ValueError("conversation payload must be object")
        result=normalize_conversation(raw)
        company_id=result["company_id"]
        target_dir=out_root/company_id
        target_dir.mkdir(parents=True,exist_ok=True)
        target=target_dir/f'{result["conversation_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written


if __name__=="__main__":
    for path in run(): print(path)
