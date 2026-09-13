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

    def __init__(self, pipeline: ConsolePipeline, company_reader: Callable[[], tuple[dict, ...]]):
        if not isinstance(pipeline, ConsolePipeline):
            raise ValueError("ConsoleHttpSurface requires ConsolePipeline")
        if not callable(company_reader):
            raise ValueError("company_reader must be callable")
        self.pipeline = pipeline
        self.company_reader = company_reader

    def handle(self, *, method: str, path: str, user_id: str, payload: dict | None = None) -> HttpResponse:
        method = method.upper().strip()
        payload = dict(payload or {})
        if not user_id.strip():
            return _json_response(401, {"ok": False, "error": "unauthorized"})

        if method == "GET" and path == "/health":
            return _json_response(200, {"ok": True, "service": "cerebro-console-gateway", "direct_model": False})

        if method == "GET" and path == "/companies":
            rows = tuple(self.company_reader())
            safe = tuple({k: row.get(k) for k in ("company_id", "name", "status") if k in row} for row in rows)
            return _json_response(200, {"ok": True, "items": safe})

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
        statuses = {200: "200 OK", 400: "400 Bad Request", 401: "401 Unauthorized", 404: "404 Not Found"}
        start_response(statuses.get(response.status, f"{response.status} Error"), list(response.headers.items()))
        return [json.dumps(response.body, separators=(",", ":")).encode("utf-8")]

    return app
