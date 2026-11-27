"""Internal PREPROD execution composition. Not an admission endpoint or IAM issuer.

Only a trusted, independently authorized runtime may inject the context resolver.
No transport, credential handling, release approval, or production execution.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import time
from typing import Callable
from console.persistent_store import ConsoleStore
from gateway import catalog_read as catalog
from gateway.catalog_audit import persist_catalog_audit
from gateway.catalog_policy import evaluate_catalog_scope
from gateway.service import GatewayRequest
from governance.policy import PolicyRequest
from identity.contracts import Identity

ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}")
SCOPE = (catalog.COMPANY,catalog.ENGINE,catalog.ENV,catalog.VERSION,catalog.CAPABILITY)

@dataclass(frozen=True)
class AuthorizedContext:
    """Verified context supplied by the existing trusted admission boundary.

    This record is NOT proof of authentication on its own. The resolver must
    verify current authority and revocation; it must never deserialize a caller
    assertion into this type without independent verification.
    """
    identity: Identity
    request_id: str
    engine_id: str
    environment: str
    version: str
    capability: str
    grant_ref: str
    issued_at: int
    expires_at: int
    facts: PolicyRequest

def blocked(reason):
    return {"status":"BLOCKED","reason":reason,"deployment_authorized":False}

class CatalogExecution:
    def __init__(self, *, store: ConsoleStore, resolve_context: Callable,
                 execution_enabled: Callable, clock=lambda: int(time.time())):
        if type(store) is not ConsoleStore or not all(callable(x) for x in
            (resolve_context,execution_enabled,clock)):
            raise ValueError("TRUSTED_RUNTIME_PORTS_REQUIRED")
        self._store=store
        self._resolve=resolve_context
        self._enabled=execution_enabled
        self._clock=clock

    def _context(self, request_id):
        if self._enabled() is not True:
            raise PermissionError("EXECUTION_DISABLED")
        now=self._clock()
        ctx=self._resolve(request_id)
        if type(ctx) is not AuthorizedContext or type(ctx.identity) is not Identity:
            raise PermissionError("AUTHORITY_CONTEXT_REQUIRED")
        if (ctx.identity.company_id,ctx.engine_id,ctx.environment,ctx.version,ctx.capability)!=SCOPE:
            raise PermissionError("AUTHORITY_SCOPE_DENIED")
        if ctx.request_id!=request_id or ctx.identity.status!="ACTIVE":
            raise PermissionError("AUTHORITY_SCOPE_DENIED")
        if any(type(v) is not str or not ID.fullmatch(v) for v in
               (ctx.identity.identity_id,ctx.grant_ref)):
            raise PermissionError("AUTHORITY_REFERENCE_INVALID")
        if any(type(v) is not int for v in (now,ctx.issued_at,ctx.expires_at)) or not (
            0<=ctx.issued_at<=now<ctx.expires_at<=ctx.issued_at+900):
            raise PermissionError("AUTHORITY_EXPIRED")
        return ctx,now

    def execute(self, request, *, request_id):
        return self._execute(request, request_id=request_id, verify_receipt=None)

    def execute_verified(self, request, *, request_id, read_signed_receipt, tribunal_issuer,
                         tribunal_public_key):
        """Require a verified independent readback in the PREPROD candidate."""
        try:
            from core.minimum.catalog_receipt import catalog_receipt_verifier
            verify_receipt = catalog_receipt_verifier(read_signed_receipt=read_signed_receipt,
                issuer=tribunal_issuer, public_key=tribunal_public_key)
        except (ImportError, TypeError, ValueError):
            return blocked("AUDIT_RECEIPT_REQUIRED")
        return self._execute(request, request_id=request_id, verify_receipt=verify_receipt)

    def _execute(self, request, *, request_id, verify_receipt):
        if type(request) is not GatewayRequest or (
            request.company_id,request.engine_id,request.environment,request.version,request.capability)!=SCOPE:
            return blocked("SCOPE_DENIED")
        if type(request_id) is not str or not ID.fullmatch(request_id):
            return blocked("REQUEST_ID_INVALID")
        try:
            if not Path(self._store.path).is_file():
                return blocked("AUDIT_STORE_UNAVAILABLE")
            ctx,_=self._context(request_id)
            def still_current():
                current,now=self._context(request_id)
                if current!=ctx:
                    raise PermissionError("AUTHORITY_CHANGED")
                return now
            def policy(req):
                still_current()
                p=evaluate_catalog_scope(req,selected_company_id=ctx.identity.company_id,facts=ctx.facts)
                return p["decision"]=="ALLOW",(p["reasons"] or [None])[0]
            def audit(row):
                now=still_current()
                return persist_catalog_audit(self._store,request_id=request_id,
                    user_id=ctx.identity.identity_id,now_epoch=now,row=row,
                    grant_ref=ctx.grant_ref if verify_receipt is not None else None)
            result=catalog.read_catalog(request,policy_check=policy,audit_sink=audit)
            if result.get("status")!="CATALOG_READ":
                return result
            if verify_receipt is not None:
                receipt_ref = verify_receipt(context=ctx, result=result.copy(), clock=self._clock)
                if not isinstance(receipt_ref, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", receipt_ref):
                    return blocked("AUDIT_RECEIPT_UNVERIFIED")
                result = {**result, "receipt_ref": receipt_ref}
            still_current()
            return result
        except Exception:
            return blocked("TRUSTED_RUNTIME_UNAVAILABLE")
