# TECH-SCOUT · PRIVATE GATEWAY ADAPTER · LAB ONLY

**Status:** CODE DEFINED, DISABLED. **Do not mark as Gateway E2E**, and do not merge or deploy without controlled review.

## Real upstream receipts
- Vercel WIF catalogue read PASS: `dpl_HP1LJVq9p3gxcFaJLuasswuxxZUT`.
- Vercel WIF isolated inbox write/read/clear PASS: `dpl_C8WF22gVnah2CScGFCh9VELY6js2`.
- Official open API reachability: 12 HTTP200, 2 timeouts `dpl_HUYnr3aFRsoAqsTyejRnxCYW7ko7`.
- GDELT DOC timeout 10.5s, GDELT feed HTTP200 `dpl_Ji6619YbibPUiG4Nm3qn6iARce2e`.
- Overpass alternative private.coffee timeout 8.2s `dpl_6W6nY3ZAjdWVZt7Lr8awBTbJTfU5`.

## Source data
- Master sheet **readonly** for machine identity: `1pNuY617Mi7DoBGvU8jVh9T58A5-Q7ACY5QPfHBfdcvw`.
- INBOX with technical writer grant only: `1lI2OgtFT-1PpGyMpku9DFZ6fbQIjVirTtlxAO747l0Q`.
- Service identity: `cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com`.

## Integration contract
Preserve existing Cloudflare FACT001 Gateway and Knowledge Bridge. Add TECHSCOUT.READ and TECHSCOUT.PROPOSE only in parallel and never make the privileged Vercel preview URL a callable public API. The existing connector registry does **routing only**, not authenticated execution. Existing CEREBRO gateway must authenticate runtime caller, validate tenant grant and policy, enforce exact allowlists and idempotent append-only proposals, apply limits and audit every execution before enabling. Do not share a personal credential in email, chat or a Sheet.

## Promotion gates
1. Snapshot contracts + backups of Gateway Worker; compare OLD/NEW route behavior.
2. Wire private authenticated Gateway→connector with machine identity and an audit sink.
3. Verify negative tests (wrong company, wrong environment, disabled, repeated idempotency key, missing grant).
4. Perform E2E through actual CEREBRO Gateway, with evidence receipt in Drive.
5. Roll back and verify; no PROD or autonomous scheduling until full tribunal gate.

## Cost and licensing
No new subscriptions; platform consumption not certified zero. Upstream rate limits, license and attribution checks still required. Use only non-protected public Catastro endpoints; prohibit mass extraction. Do not feed personal information into QuickChart URL or other public endpoint. For images verify object-level licensing.
