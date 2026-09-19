from __future__ import annotations

import json
import os
from pathlib import Path

MANDATORY_ENGINES=(
    "CORE-001","SUP-001","OBSERV-001","INC-001","SELF-001","SEC-001","IAM-001",
    "QA-001","QAB-001","REG-001","DR-001","RBLD-001","BCP-001","CRS-001",
    "KNW-001","PRV-001","LRN-001","RSH-001","UPD-001","OBS-001","RAG-001",
    "CACHE-001","SIM-001","TWIN-001","FINOPS-001"
)

def _load_companies(path:Path)->list[dict]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,list): raise ValueError("company config must be list")
    seen=set()
    out=[]
    for item in payload:
        if not isinstance(item,dict): raise ValueError("company config item must be object")
        cid=str(item.get("company_id","")).strip()
        if not cid or cid in seen: raise ValueError("company_id must be unique and non-empty")
        seen.add(cid)
        out.append(item)
    return out

def build_registry(config_path:Path)->dict:
    companies=[]
    for item in _load_companies(config_path):
        companies.append({
            "company_id":str(item["company_id"]),
            "legal_name":str(item.get("legal_name","")),
            "environment":str(item.get("environment","LAB")).upper(),
            "version":str(item.get("version","1.0.0")),
            "autonomy_profile":str(item.get("autonomy_profile","")),
            "enabled":bool(item.get("enabled",True)),
            "engine_id":"COMP-REG-001",
            "status":"REGISTERED",
        })
    return {
        "record_type":"company_registry",
        "engine_id":"COMP-REG-001",
        "companies":companies,
        "company_count":len(companies),
        "cross_company_default":"DENY",
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def build_activation_matrix(config_path:Path)->dict:
    rows=[]
    for item in _load_companies(config_path):
        cid=str(item["company_id"])
        enabled=bool(item.get("enabled",True))
        rows.append({
            "company_id":cid,
            "engine_id":"ENGACT-001",
            "environment":str(item.get("environment","LAB")).upper(),
            "version":str(item.get("version","1.0.0")),
            "required_engines":list(MANDATORY_ENGINES),
            "activation_state":"DECLARED" if enabled else "DISABLED",
            "automatic_prod_activation_allowed":False,
            "external_mutation_allowed":False,
        })
    return {
        "record_type":"company_engine_activation_matrix",
        "engine_id":"ENGACT-001",
        "rows":rows,
        "automatic_prod_activation_allowed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    cfg=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    out=Path(os.environ.get("CEREBRO_COMPANY_REGISTRY_ROOT",".cerebro-runtime/company-registry"))
    out.mkdir(parents=True,exist_ok=True)
    registry=build_registry(cfg)
    matrix=build_activation_matrix(cfg)
    p1=out/"registry.json"; p2=out/"activation-matrix.json"
    p1.write_text(json.dumps(registry,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    p2.write_text(json.dumps(matrix,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return [p1,p2]

if __name__=="__main__":
    for p in run(): print(p)
