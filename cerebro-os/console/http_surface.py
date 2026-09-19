from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Mapping

try:
    from .pipeline import ConsolePipeline
except ImportError:  # direct module loading from cerebro-os/console in tests/runtime
    from pipeline import ConsolePipeline


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: dict
    headers: Mapping[str, str]


def _json_response(status: int, body: dict) -> HttpResponse:
    return HttpResponse(
        status=status,
        body=body,
        headers={
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            "x-cerebro-gateway": "required",
        },
    )


class ConsoleHttpSurface:
    """Zero-dependency HTTP boundary for CEREBRO Console V0.

    Commands execute only through ConsolePipeline:
    CONSOLE -> GATEWAY -> POLICY -> ENGINE -> AUDIT.
    """

    def __init__(
        self,
        pipeline: ConsolePipeline,
        company_reader: Callable[[], tuple[dict, ...]],
        context_reader: Callable[[str], tuple[dict, ...]] | None = None,
        engine_reader: Callable[[str], tuple[dict, ...]] | None = None,
        history_reader: Callable[[str], tuple[dict, ...]] | None = None,
        audit_reader: Callable[[str], tuple[dict, ...]] | None = None,
        access_reader: Callable[[str], tuple[dict, ...]] | None = None,
        onboarding_reader: Callable[[], dict] | None = None,
    ):
        if not isinstance(pipeline, ConsolePipeline):
            raise ValueError("ConsoleHttpSurface requires ConsolePipeline")
        if not callable(company_reader):
            raise ValueError("company_reader must be callable")
        readers = (context_reader, engine_reader, history_reader, audit_reader, access_reader)
        if any(reader is not None and not callable(reader) for reader in readers):
            raise ValueError("optional console readers must be callable")
        if onboarding_reader is not None and not callable(onboarding_reader):
            raise ValueError("onboarding_reader must be callable")
        self.pipeline = pipeline
        self.company_reader = company_reader
        self.context_reader = context_reader or (lambda _company_id: ())
        self.engine_reader = engine_reader or (lambda _company_id: ())
        self.history_reader = history_reader or (lambda _company_id: ())
        self.audit_reader = audit_reader or (lambda _company_id: ())
        self.access_reader = access_reader or (lambda _company_id: ())
        self.onboarding_reader = onboarding_reader or (lambda: {})

    def handle(self, *, method: str, path: str, user_id: str, payload: dict | None = None) -> HttpResponse:
        method = method.upper().strip()
        payload = dict(payload or {})
        if not user_id.strip():
            return _json_response(401, {"ok": False, "error": "unauthorized"})

        if method == "GET" and path == "/health":
            return _json_response(200, {"ok": True, "service": "cerebro-console-gateway", "direct_model": False})

        if method == "GET" and path == "/onboarding/queue":
            row = self.onboarding_reader()
            if not isinstance(row, dict):
                return _json_response(500, {"ok": False, "error": "invalid_onboarding_reader"})
            allowed = (
                "engine_id","status","human_reason","environment","version",
                "worker_autonomous","stale_lease_reclaim_supported","queue_stats","cost_eur",
            )
            safe = {key: row.get(key) for key in allowed if key in row}
            return _json_response(200, {"ok": True, "onboarding": safe})

        if method == "GET" and path == "/companies":
            rows = tuple(self.company_reader())
            safe = tuple({k: row.get(k) for k in ("company_id", "name", "status") if k in row} for row in rows)
            return _json_response(200, {"ok": True, "items": safe})

        scoped_routes = {
            "/contexts/": (self.context_reader, ("context_type", "context_id", "label", "status")),
            "/engines/": (self.engine_reader, ("engine_id", "name", "status", "environment", "version")),
            "/history/": (self.history_reader, ("request_id", "engine_id", "status", "evidence_ref", "environment", "version")),
            "/audit/": (self.audit_reader, ("request_id", "engine_id", "action", "result", "evidence_ref", "timestamp")),
            "/access/": (self.access_reader, ("engine_id", "status", "human_reason", "environment", "version", "accounts_total", "authenticated_accounts", "credentialed_accounts", "connector_account_count", "online_bridge_profiles")),
        }
        if method == "GET":
            for prefix, (reader, allowed_fields) in scoped_routes.items():
                if path.startswith(prefix):
                    company_id = path[len(prefix):].strip("/")
                    if not company_id:
                        return _json_response(400, {"ok": False, "error": "company_id_required"})
                    rows = tuple(reader(company_id))
                    safe = tuple(
                        {key: row.get(key) for key in allowed_fields if key in row}
                        for row in rows
                        if isinstance(row, dict) and row.get("company_id", company_id) == company_id
                    )
                    return _json_response(200, {"ok": True, "company_id": company_id, "items": safe})

        if method == "POST" and path == "/commands":
            command = {
                "request_id": payload.get("request_id"),
                "user_id": user_id,
                "company_id": payload.get("company_id"),
                "context_type": payload.get("context_type"),
                "message": payload.get("message"),
                "environment": payload.get("environment", "LAB"),
                "version": payload.get("version", "1.0.0"),
            }
            try:
                result = self.pipeline.execute(command)
            except ValueError as exc:
                return _json_response(400, {"ok": False, "error": "invalid_command", "detail": str(exc)})
            return _json_response(200, {"ok": True, "result": result})

        return _json_response(404, {"ok": False, "error": "route_not_found"})


def _default_identity_resolver(environ: Mapping[str, object]) -> str:
    """Read identity only from a trusted WSGI/upstream-auth slot.

    Deliberately does not trust HTTP_X_CEREBRO_USER_ID or any other
    browser-controlled identity header. A production reverse proxy/IAM layer
    must authenticate the request first and inject REMOTE_USER (or supply an
    explicit resolver to wsgi_app).
    """

    return str(environ.get("REMOTE_USER", "") or "").strip()


def wsgi_app(
    surface: ConsoleHttpSurface,
    identity_resolver: Callable[[Mapping[str, object]], str] | None = None,
):
    """Minimal stdlib-compatible WSGI adapter with fail-closed identity.

    The browser never supplies the authoritative user id in JSON or a trusted
    custom header. Upstream IAM must establish identity and expose it via
    REMOTE_USER, or callers must inject a resolver that performs equivalent
    trusted verification.
    """

    resolve_identity = identity_resolver or _default_identity_resolver
    if not callable(resolve_identity):
        raise ValueError("identity_resolver must be callable")

    def app(environ, start_response):
        method = str(environ.get("REQUEST_METHOD", "GET"))
        path = str(environ.get("PATH_INFO", "/"))
        try:
            user_id = str(resolve_identity(environ) or "").strip()
        except Exception:
            user_id = ""
        payload = {}
        if method.upper() == "POST":
            try:
                length = min(int(environ.get("CONTENT_LENGTH") or 0), 65536)
                raw = environ["wsgi.input"].read(length) if length else b""
                payload = json.loads(raw.decode("utf-8")) if raw else {}
                if not isinstance(payload, dict):
                    raise ValueError("payload must be object")
            except Exception:
                response = _json_response(400, {"ok": False, "error": "invalid_json"})
                start_response("400 Bad Request", list(response.headers.items()))
                return [json.dumps(response.body).encode("utf-8")]
        response = surface.handle(method=method, path=path, user_id=user_id, payload=payload)
        statuses = {200: "200 OK", 400: "400 Bad Request", 401: "401 Unauthorized", 404: "404 Not Found", 500: "500 Internal Server Error"}
        start_response(statuses.get(response.status, f"{response.status} Error"), list(response.headers.items()))
        return [json.dumps(response.body, separators=(",", ":")).encode("utf-8")]

    return app
