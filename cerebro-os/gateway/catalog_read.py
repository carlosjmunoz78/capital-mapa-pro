"""Production-intended, offline PREPROD catalog capability. No live ingress.

Uses the real versioned global definitions, not FACT.INVENTORY.READ's fixture.
The caller is a trusted runtime adapter, never a request-supplied authorizer.
This module is not wired to owner admission or to a deployed service.
"""
from hashlib import sha256
from pathlib import Path
import json
from connectors.registry import ConnectorRegistry, ConnectorCapability
from gateway.service import Gateway, GatewayRequest
from registry.canonical_loader import load_canonical_registry

CAPABILITY="FACT.CATALOG.READ"
VERSION="1.2.0"
COMPANY="fenix"
ENGINE="FACT-001"
ENV="PREPROD"
SOURCE_SHA256="1c566602c5ecc7df815c7653d77f8dad65b5e12eca8017d060b5764e7d488b03"
SOURCE=Path(__file__).resolve().parents[1]/"registry"/"canonical_177.json"

def read_catalog(request, *, policy_check, audit_sink):
    """No external actions. Trusted runtime must check membership/IAM per request.
    Audit must complete before any response containing catalog is returned.
    """
    def denied(reason):
        return {"status":"BLOCKED","reason":reason,"deployment_authorized":False}
    if type(request) is not GatewayRequest or (request.company_id,request.engine_id,
        request.capability,request.environment,request.version)!=(COMPANY,ENGINE,CAPABILITY,ENV,VERSION):
        return denied("SCOPE_DENIED")
    if not callable(policy_check) or not callable(audit_sink):
        return denied("TRUSTED_RUNTIME_REQUIRED")
    connectors=ConnectorRegistry()
    connectors.register(ConnectorCapability("fact-catalog-local",CAPABILITY,"SCRIPT",
        company_id=COMPANY,environment=ENV,version=VERSION))
    def checked(req):
        allowed,reason=policy_check(req)
        return allowed is True,reason
    try:
        route=Gateway({ENGINE},connectors,checked).route(request)
        if route.get("status")!="ROUTED":
            return denied("POLICY_OR_ROUTE_DENIED")
        blob=SOURCE.read_bytes()
        if sha256(blob).hexdigest()!=SOURCE_SHA256:
            return denied("CATALOG_SOURCE_DRIFT")
        # Validate using the existing canonical loader, which enforces 177 unique IDs.
        data=load_canonical_registry(SOURCE)
        if SOURCE.read_bytes()!=blob or data!=json.loads(blob):
            return denied("CATALOG_SOURCE_DRIFT")
        result={"status":"CATALOG_READ","company_id":COMPANY,"engine_id":ENGINE,
            "environment":ENV,"version":VERSION,"capability":CAPABILITY,
            "catalog_scope":"GLOBAL_LOGICAL_DEFINITIONS","source_schema":data["schema_version"],
            "source_sha256":SOURCE_SHA256,"engine_ids":tuple(data["engine_ids"]),
            "count":len(data["engine_ids"]),"operational_instances_certified":False,
            "external_mutation_allowed":False,"deployment_authorized":False}
        audit={"company_id":COMPANY,"engine_id":ENGINE,"environment":ENV,
            "version":VERSION,"capability":CAPABILITY,"status":result["status"],
            "source_sha256":SOURCE_SHA256,"result_sha256":sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()}
        # Trusted sink has explicit completion contract; no implicit success.
        if audit_sink(audit) is not True:
            return denied("AUDIT_UNCONFIRMED")
        return result
    except Exception:
        return denied("RUNTIME_OR_AUDIT_UNAVAILABLE")
