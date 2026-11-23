# CP82 · JARVIS → FACT private read proof gate

**Scope:** LAB only, no public route, no Cloudflare mutation. Base CP81 `8b053d256a787c4ee167a98d307fa8ba4191c5b4`.

## Verified independent live facts
Connected Cloudflare Access account authenticated the owner on JARVIS LAB (event 2026-11-23 01:13:33 UTC). FACT-001 recovery LAB D1 has 12 completed provider inventory jobs for `fenix-capital`, one RECONCILE, and 38 P5 audit records. These are separate observations, **NOT an end-to-end request**. Existing JARVIS Workers have no verified service binding to FACT, both JARVIS and FACT Gateway flags OFF.

## Executable acceptance contract
`gateway/remote_read_proof_cp82.py` offers a hard-fail classifier and a future two-party receipt verification gate. To accept a real private read: (1) JARVIS policy signed envelope with owner/IAM proof; (2) independent FACT-signed response with same request, company, environment, capability, version and timestamp; (3) independently retrieved durable FACT receipt matching the signed response; (4) different 32-byte minimum HMAC keys resolved from an external Vault, never request payload; (5) read-only, zero extra cost, LAB-only. The capability `FACT.INVENTORY.READ` is a CP82 **proposed contract**, not an existing exposed FACT RPC. A valid proof pair does not itself permit PROD promotion.

## External consumers inventory
See `evidence/cp82_external_live_observation.json` for exact inspected repository refs and partial scope. GitHub code search on default branches returned no exact `OnboardingQueue` / `claim_attempts` matches in App but is not exhaustive (indexes, nondefault branches, indirect RPC clients), and social code search was incomplete. Thus external consumer gate remains **POR AUDITAR**.

## Activation gates and rollback
No secrets, routes, new Workers, D1 databases, crons, publications, PROD changes or new subscriptions created. The signed receipt is not available, so no E2E green. Rollback: revert this branch commit or reset it to CP81 base. Next: inventory external running consumers from deployed App/CRM/Workers, validate read-only IAM credential and private Service Binding in a separate isolated canary; then issue a real LAB request and independently read FACT's correlated receipt. Preserve Cloudflare and App original behavior.
