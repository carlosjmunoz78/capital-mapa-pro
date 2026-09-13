# CEREBRO OS · Observability zero-cost auxiliary sink · 2026-09-14

## Scope
Parallel, non-destructive observability path intended to keep heavy auxiliary logs outside the Supabase transactional core where practical. No PROD wiring is claimed by this document.

## HECHO / evidenced
- `cerebro-os/runtime/zero_cost_observability_sink.py` implements an append-only JSONL auxiliary sink with no external subscription requirement.
- Every accepted event requires `company_id`, `engine_id`, `environment`, `version` and one of `log`, `metric`, `incident`.
- Secret-like fields (`password`, `secret`, tokens, API keys, authorization, cookies, service role/private keys and variants) are rejected before persistence.
- Replay validates every stored envelope and fails closed on corrupt JSONL.
- Scope filtering by company/engine/environment/version is implemented.
- `cerebro-os/tests/test_zero_cost_observability_sink.py` proves persistence/replay, multiempresa scope, log+metric+incident coverage, secret rejection and corruption fail-closed behavior.
- Factory CI run `34788667726`, job `verify`, completed **SUCCESS** with the complete unit-test suite.
- Additional recurring cost of this LAB/local/runner sink: **0 EUR**.

## PARCIAL / not proven
- The JSONL sink is not yet wired to live PROD engines.
- No claim is made that all 177 engines emit live PROD logs, metrics and incidents into this sink.
- A persistent PROD host/path with backup/retention/rotation is not yet evidenced.
- Existing PROD observability tables remain preserved; this sink is parallel and must not replace them destructively.

## Promotion gate for PROD mirroring
Before wiring: identify host/storage already contracted or free, define retention/rotation and disk-failure behavior, verify no secret leakage, preserve existing observability tables, implement parallel writes, compare OLD vs NEW, test rollback by disabling the mirror only, and then collect per-engine live coverage evidence.

## State
- Auxiliary sink contract: **HECHO / GREEN_CODE_CI**.
- Multiempresa envelope: **HECHO / GREEN_CI**.
- Secret filtering: **HECHO / GREEN_CI**.
- Replay/corruption handling: **HECHO / GREEN_CI**.
- PROD mirror deployment: **PARCIAL / NOT PROVEN**.
- 177-engine live PROD coverage: **PARCIAL / NOT PROVEN**.
- Cost introduced now: **0 EUR**.
