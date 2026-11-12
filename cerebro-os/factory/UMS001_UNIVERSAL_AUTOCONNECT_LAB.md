# FACT-001 → UMS-001 · Factory-first universal integration

**LAB code only** · additive change to existing `factory.py`, branch `cerebro-engine-factory-v0`.

- Every newly scaffolded engine inherits the same `media_gateway` manifest and two generated files: `config/ums001_universal_media.json`, `events/MEDIA_JOB_REQUESTED.contract.json`.
- No new per-engine Worker, queue, API subscription or separate media integration.
- Default is `PENDING_FACTORY_IAM`, NOT active media dispatch. A factory-signed enrollment into the real CEREBRO Gateway issuer registry is still required to make future engines operational automatically. Enrollment cannot be inferred from a self-declared `engine_id`.
- `company_id`, `engine_id`, `environment`, `version`, permitted capability, budget, signed identity, and anti-replay are required.
- Existing engines unchanged; no migration; no PROD modification.
- Current Cloudflare UMS-001 universal Gateway has issuer registry pinned to a CANARY account and `REGISTRATION_WINDOW_ENABLED=false`. FACT-001 Cloudflare Gateway `GATEWAY_ENABLED=false`. Do not bypass either until Factory provisioning is verified.
- Action needed for full automation: authenticate FACT-001 as a trusted *enrollment service* once; make the Gateway consume enrollment events and provision key IDs and policies from Factory manifests with rollback/audit; prevent unauthorized self-enrollment. Afterward this scaffold supplies the standard contract without modifying the factory for each new engine.

**Important:** The integrated implementation is not fully live until a new test engine is generated and its signing identity is enrolled and used successfully in a real media request across the whole chain.
