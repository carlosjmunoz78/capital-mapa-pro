# TECH-SCOUT isolated Cloudflare RPC · LAB scaffold (OFF)

Source files:
- `sources.mjs`: 14 public providers as **fixed GET endpoints**; strict schema + tenant/environment validation; no dynamic URL or body; bounded result; audit in existing LAB KV namespace under `techscout/v0.1.0/probe/`.
- `index.mjs`: Cloudflare WorkerEntrypoint RPC; public HTTP fetch always 403. No workers.dev, preview routes or cron. Default disabled; `propose()` ALWAYS DENIED until Gateway->INBOX integration and audit are verified.
- `tests/test_techscout_public_sources.mjs`: isolated pure-function regression tests for fail closed, SSRF, idempotency and schema.

**Important:** KV is eventually consistent. Its lookup cannot guarantee atomic exactly-once semantics; only used for low-risk READ_ONLY probes in LAB. Do NOT use it as a substitute for transactional idempotency on proposals/writes.

**Activation gates**: (1) attach service binding from a parallel safe Gateway, (2) create a dedicated secret `TECHSCOUT_CALLER_TOKEN` for trusted caller; never put in docs, (3) grant authenticated caller context and audit sink; (4) verified E2E actual FACT Gateway->Worker, negative tests + rollback, (5) only then set `TECHSCOUT_ENABLED=true`, `TECHSCOUT_PUBLIC_PROBE_ENABLED=true`. The required grants and secrets do not currently exist, so the worker must remain OFF.

Overpass is disabled after repeated timeouts. GDELT uses its HTTP200 feed as status proof, NOT its unreliable DOC query. Catastro uses only discovery WSDL; mass extraction disallowed. Openverse media usage requires item-level license checks. No tokens, passwords, customer data, PROD, nor any self-driving jobs.

**Current factory:** Branch `cerebro/techscout-private-gateway-lab-20261121`, parent `cerebro-engine-factory-v0`. No merge to production. Use platform existing resources without new subscriptions; Cloudflare KV shares existing LAB namespace with a strict per-engine prefix.
