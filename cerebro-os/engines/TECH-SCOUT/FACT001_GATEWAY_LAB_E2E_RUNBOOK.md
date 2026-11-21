# FACT-001 original Cloudflare Gateway → TECH-SCOUT · LAB E2E

**Verified:** 2026-11-21 · **Status:** FACT001 original LAB Gateway read-only API integration **E2E PASS**. Production promotion and credential autoprov still **NOT DONE**.

## Original assets preserved

- Original Worker: `cerebro-fact001-gateway-lab-eu-20261109`. No public worker.dev URL, preview URL, cron or production route.
- Immutable baseline version: `a7bfd49b-f0ee-448f-b7e2-75e5512feee8`.
- Current verified version: `8f35e224-b7a9-4f16-8b72-23555743d4c0`.
- Seven source modules before, eight after. Six auxiliary modules are byte-identical. The old `fact001-media-gateway-lab.mjs` is preserved except for one import, one isolated queue branch, and one guarded RPC method.
- All 18 existing Cloudflare bindings preserved; added `TECHSCOUT` Service Binding to `cerebro-techscout-public-sources-lab`, `TECHSCOUT_CALLER_TOKEN` dedicated private secret, `TECHSCOUT_FACT001_ENABLED` flag. Existing NIA/UMS flags preserved.
- Safety: existing `GATEWAY_ENABLED=false`, `NIA_ISSUER_ENABLED=true`, `UMS001_QUEUE_ENABLED=true` remained unchanged; nothing added to PROD, App, CRM, GitHub Actions, or Enterprise.

## Implementation

Original worker's main module adds:

```js
import {FACT_TECHSCOUT_QUEUE,factTechscoutProbe} from './fact001-bridge.mjs';
```

Inside the existing `async queue(batch,env)` handler, before the original NIA and UMS routes:

```js
if(batch.queue===FACT_TECHSCOUT_QUEUE){
  for(const msg of batch.messages){
    try {
      const r=await factTechscoutProbe(env,msg.body);
      console.log('FACT_TECHSCOUT_STATUS='+r.status);
      msg.ack();
    } catch {
      console.log('FACT_TECHSCOUT_STATUS=BLOCKED');
      msg.ack();
    }
  }
  return;
}
```

Inside existing `CEREBROFactUMS001Lab extends WorkerEntrypoint`:

```js
async techscoutProbeFromRuntime(command,callerToken){
  if(!await sameToken(callerToken,this.env.CEREBRO_RUNTIME_CALLER_TOKEN))
    throw Error('FACT_TECHSCOUT_RUNTIME_AUTH_DENIED');
  return factTechscoutProbe(this.env,command);
}
```

The imported `fact001-bridge.mjs` is maintained in this branch under `cerebro-os/engines/TECH-SCOUT/`. The method is a private RPC, not a public HTTP API.

## E2E receipts

Cloudflare Queue EU `cerebro-techscout-fact001-e2e-lab-eu` (id `4d433391c19545e88cc2a0fe52ddf11f`) has one consumer connected to the original FACT001 LAB Gateway, batch size 1 and maximum concurrency 1.

- `techscout_fact001_original_world_bank_20261121_v1`: original Gateway receipt PASS HTTP 200; TECH-SCOUT receiver receipt PASS HTTP 200.
- `techscout_fact001_original_quickchart_20261121_v1`: original Gateway receipt PASS HTTP 200; TECH-SCOUT receiver receipt PASS HTTP 200.
- Negative tenant command and PROD command rejected without generating downstream audit records. Duplicate request id was not re-executed and preserved its original receipt. Queue backlog 0.
- Independent earlier shadow proof used a separate `cerebro-fact001-techscout-shadow-lab` Worker with the same patch.

KV receipt prefixes on existing LAB namespace:
- `techscout/fact001/v0.1.0/<request_id>`
- `techscout/v0.1.0/probe/<request_id>`

## Rollback physically verified

Deployment `a7bfd49b-f0ee-448f-b7e2-75e5512feee8` restored to 100% and read back from Cloudflare API. Re-deployed the verified version `8f35e224-b7a9-4f16-8b72-23555743d4c0` at 100% and read it back: **ROLLBACK_AND_RESTORE_PASS**. No source or credential backup exported in plaintext.

If emergency rollback needed again, deploy immutable baseline version via Cloudflare Workers Deployments API; verify API flags and queue routing thereafter. Keep TECH-SCOUT queue consumer isolated from NIA/UMS.

## Supported now vs not supported

**Supported on demand in LAB:** authenticated, private, low-volume `TECHSCOUT.PROBE` for WORLD_BANK, QUICKCHART, COMMONS, GDELT feed (not GDELT DOC), only one fixed URL per provider; no arbitrary URLs, no personal data, no paid API calls. Original FACT001 E2E confirmed on two representative providers; parallel gateway E2E confirmed on four. Master catalogue read and isolated INBOX reversible write already proven independently through Google WIF on Vercel LAB.

**Not yet supported:** Automatically discover, validate and activate arbitrary new third-party keys solely because the user stores them in Cloudflare Worker `cerebro-techscout-credentials-lab`. Cloudflare Worker secrets are per-script, not an account-wide credential registry. A provider-specific adapter, grants/scopes, cost/rate and policy checks are still required. No key-based provider should be marked ACTIVE before successful authenticated E2E receipt and policy approval. Auto-credential detection itself needs a private broker/service binding. `TECHSCOUT.PROPOSE` remains blocked for original FACT001 until independently audited.

**Safety detail:** read-only KV idempotency uses eventually consistent Cloudflare KV, not atomic compare-and-swap. Do not reuse this design for money, writes or paid actions.

**Costs:** no additional subscriptions. Metered consumption must stay within existing limits and be monitored; 0 euros of new fees does not certify 0 marginal usage.

**Audit source:** TECH-SCOUT master spreadsheet, `Validación API` and `Continuidad` tabs, and Drive technical journal.
