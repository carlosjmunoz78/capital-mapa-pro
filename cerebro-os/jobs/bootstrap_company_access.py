from __future__ import annotations
import hashlib,json,os
from pathlib import Path

ENGINE_ID="ACCESSBOOT-001"
FORBIDDEN_SECRET_KEYS={"password","token","api_key","secret","secret_value","raw_secret","credential_value"}

def _reject_raw_secrets(value):
    if isinstance(value,dict):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_SECRET_KEYS:
                raise ValueError(f"raw secret field forbidden: {key}")
            _reject_raw_secrets(child)
    elif isinstance(value,list):
        for child in value:
            _reject_raw_secrets(child)

def bootstrap_company_access(payload:dict)->dict:
    _reject_raw_secrets(payload)
    company_id=str(payload.get("company_id","")).strip()
    if not company_id:
        raise ValueError("company_id required")
    environment=str(payload.get("environment","LAB")).upper()
    version=str(payload.get("version","1.0.0"))
    if environment not in {"LAB","PREPROD"}:
        raise ValueError("ACCESSBOOT-001 supports LAB/PREPROD only")

    requirements=payload.get("requirements") or []
    requirements_inventory_complete=bool(requirements) or bool(payload.get("requirements_inventory_complete",False))
    accounts=payload.get("existing_accounts") or []
    connectors=payload.get("existing_connectors") or []
    sessions=payload.get("session_observations") or []
    for name,rows in (("requirements",requirements),("existing_accounts",accounts),("existing_connectors",connectors),("session_observations",sessions)):
        if not isinstance(rows,list):
            raise ValueError(f"{name} must be list")
        for row in rows:
            if not isinstance(row,dict):
                raise ValueError(f"{name} item must be object")
            if name!="requirements" and str(row.get("company_id",""))!=company_id:
                raise ValueError(f"cross-company {name} denied")

    account_caps=set()
    for row in accounts:
        for cap in row.get("capabilities") or []:
            account_caps.add(str(cap).strip())
    connector_caps=set()
    for row in connectors:
        if row.get("active",True):
            cap=str(row.get("capability","")).strip()
            if cap: connector_caps.add(cap)
    authenticated_providers={
        str(row.get("provider","")).strip()
        for row in sessions if row.get("authenticated") and str(row.get("provider","")).strip()
    }

    rows=[]
    for req in requirements:
        capability=str(req.get("capability","")).strip()
        purpose=str(req.get("purpose","")).strip()
        provider=str(req.get("provider","")).strip()
        required=bool(req.get("required",True))
        if not capability or not purpose:
            raise ValueError("access requirement capability/purpose required")
        if capability in connector_caps:
            status="SATISFIED_EXISTING_CONNECTOR"
        elif capability in account_caps:
            status="SATISFIED_EXISTING_ACCOUNT"
        elif provider and provider in authenticated_providers:
            status="AUTHENTICATED_SESSION_DISCOVERED"
        else:
            status="DISCOVERY_REQUIRED"
        rows.append({
            "capability":capability,"purpose":purpose,"provider":provider,"required":required,
            "status":status,"account_creation_allowed":False,"secret_value_required":False,
        })

    missing=[x for x in rows if x["required"] and x["status"]=="DISCOVERY_REQUIRED"]
    ready=requirements_inventory_complete and not missing
    reason=None if ready else ("ACCESS_REQUIREMENTS_INVENTORY_REQUIRED" if not requirements_inventory_complete else "REQUIRED_ACCESS_DISCOVERY_PENDING")
    canonical=json.dumps({"company_id":company_id,"environment":environment,"version":version,"requirements":rows},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_access_bootstrap","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":environment,"version":version,"requirements":rows,
      "requirements_inventory_complete":requirements_inventory_complete,
      "minimum_accesses_ready":ready,"missing_required_count":len(missing),
      "status":"GREEN" if ready else "PARTIAL","reason":reason,
      "strategy":"REUSE_DISCOVER_BEFORE_CREATE",
      "account_creation_allowed":False,"secret_collection_allowed":False,
      "external_mutation_allowed":False,"prod_activation_allowed":False,"cost_eur":0.0,
      "required_gates":["TENANT-001","IAM-001","POL-001","ACCESS-HLT-001"],
      "next_stage":"ACCESS_HEALTH" if ready else ("ACCESS_REQUIREMENTS_INVENTORY" if not requirements_inventory_complete else "ACCOUNT_CONNECTOR_SESSION_DISCOVERY"),
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_ACCESSBOOT_REQUEST_ROOT",".cerebro-runtime/accessboot-requests"))
    out=Path(os.environ.get("CEREBRO_ACCESSBOOT_RESULT_ROOT",".cerebro-runtime/accessboot-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=bootstrap_company_access(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
