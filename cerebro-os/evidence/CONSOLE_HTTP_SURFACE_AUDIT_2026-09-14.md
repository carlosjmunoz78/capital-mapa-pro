# CEREBRO Console V0 — HTTP surface audit — 2026-09-14

## HECHO

- `cerebro-os/console/http_surface.py` exists on `cerebro-engine-factory-v0`.
- The HTTP boundary exposes `/health`, `/companies`, and `/commands`.
- Commands are routed only through `ConsolePipeline`; the contract documents `CONSOLE -> GATEWAY -> POLICY -> ENGINE -> AUDIT`.
- The health response explicitly declares `direct_model: false`.
- Identity fails closed when no trusted user identity is provided.
- The default WSGI identity resolver trusts `REMOTE_USER` from an upstream authenticated layer and deliberately does not trust browser-controlled custom identity headers.
- Existing deploy-readiness tests require HTTP contract + web UI + profile launcher branch to be green while keeping deployable/prod promotion false until a real authenticated URL is proven.

## PARCIAL

A real externally reachable authenticated Console Gateway URL has not been proven. Therefore Console V0 is source/test ready but not production-deployed.

## SAFE NEXT

Deploy through an already-authorized, cost-neutral authenticated runtime, then prove live `/health`, authenticated `/companies`, authenticated `/commands`, profile launcher integration, audit persistence, and rollback before production promotion.

## NON-GOALS

- Do not deploy a disconnected static stub.
- Do not connect browser UI directly to a model.
- Do not trust a user id supplied by browser JSON or a browser-controlled custom header.
