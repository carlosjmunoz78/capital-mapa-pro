"""Read-only ZEUS ownership projection of existing engine definitions.

Catalog visibility is not execution permission. Do not change the canonical
registry, existing manifests, readiness evidence, or identity configuration.
"""
import json
from pathlib import Path
from registry.canonical_loader import canonical_engine_ids

POLICY=Path(__file__).resolve().parents[1]/"governance"/"zeus_resource_policy.json"

def project_shared_catalog(*, canonical_path=None, seed_path=None):
    ids=canonical_engine_ids(canonical_path)
    if seed_path is None:
        seed_path=Path(__file__).with_name("engine_registry.seed.json")
    seed=json.loads(Path(seed_path).read_text(encoding="utf-8"))
    if not isinstance(seed,list):
        raise ValueError("INVALID_SEED")
    by_id={}
    for row in seed:
        if not isinstance(row,dict):
            raise ValueError("INVALID_SEED_RECORD")
        eid=row.get("engine_id")
        if eid not in ids or eid in by_id:
            raise ValueError("INVALID_SEED_ID")
        if row.get("company_scope") not in {"GLOBAL_ONLY","GLOBAL_OR_SCOPED","COMPANY_SCOPED"}:
            raise ValueError("INVALID_SEED_SCOPE")
        by_id[eid]=row
    p=json.loads(POLICY.read_text(encoding="utf-8"))
    if (p.get("resource_owner"),p.get("orchestrator"),p.get("human_access"),p.get("execution"),
        p.get("grants_runtime_access"),p.get("grants_deployment_authority"))!=(
        "ZEUS","CEREBRO_OS","OWNER_ONLY","SCOPED_AUTHORIZED_CAPABILITIES",False,False):
        raise ValueError("RESOURCE_POLICY_DRIFT")
    return {"resource_owner":"ZEUS","orchestrator":"CEREBRO_OS",
        "catalog_visibility":"ALL_AUTHORIZED_COMPANIES","logical_engine_count":len(ids),
        "seed_record_count":len(by_id),"runtime_authorization_granted":False,
        "deployment_authorized":False,"engines":[
            {"engine_id":eid,"resource_owner":"ZEUS",
             "definition_shared":True,"execution_requires_scope":True,
             "existing_scope":by_id[eid]["company_scope"] if eid in by_id else None,
             "seed_status":by_id[eid].get("status") if eid in by_id else None,
             "runtime_verified_by_projection":False} for eid in ids]}
