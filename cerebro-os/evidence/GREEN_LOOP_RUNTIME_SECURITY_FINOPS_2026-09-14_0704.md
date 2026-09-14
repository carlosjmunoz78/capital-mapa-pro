# CEREBRO OS · GREEN LOOP EVIDENCE · 2026-09-14 07:04 Europe/Madrid

## Scope

Read-only / non-destructive evidence consolidation after APP RPC promotion. No PREPROD reactivation. No credential value storage. No payment or billing mutation. No legacy RPC EXECUTE revocation. No real communication send.

## APP PROD runtime

- APP main promoted commit: `dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c`.
- PROD Live Deploy run `34790008072`: SUCCESS.
- PROD Runtime Smoke run `34790008059`: SUCCESS.
- Runtime smoke green steps include:
  - production frontend compilation;
  - bundle bound to canonical PROD and not PREPROD;
  - `https://app.fenixcapital.es` serves deployed frontend;
  - live domain serves exact main SHA;
  - `fenix-app-gateway` health is PROD and reachable;
  - gateway fails closed without user identity;
  - directory/economy APIs fail closed anonymously;
  - retired migration endpoints remain unavailable;
  - Ana API CORS preflight succeeds;
  - Ana Notion secret presence is verified without exposing the value.

## Cloudflare topology evidence

For promoted SHA `dd09153a...` GitHub check-runs show:

- `Workers Builds: fenix-capital-inmo-map`: SUCCESS.
- `Workers Builds: fenix-capital-inmo-maps`: SUCCESS.
- `Cloudflare Pages`: FAILURE.
- GitHub `PROD Live Deploy`: SUCCESS.
- APP runtime smoke on the live domain: SUCCESS and exact SHA match.

Disposition: the Cloudflare Pages failure is recorded as a parallel deployment-topology defect, but current APP availability/source provenance is independently green. Do not delete or disable Cloudflare resources until routing/dependency ownership is proven.

## Supabase security advisor refresh

Observed at approximately `2026-09-14T05:04:48Z` on project `cluhljgonannaafpmblx`:

- `rls_enabled_no_policy`: 44 INFO findings. Existing posture remains fail-closed for direct table access; do not bulk-add permissive policies.
- `authenticated_security_definer_function_executable`: 24 WARN findings. Do not bulk revoke. Selective retirement remains gated on authenticated HTTP E2E + rollback evidence + caller classification.
- `extension_in_public`: one WARN for `pg_net` in `public`; dependency-safe move not yet proven.
- `auth_leaked_password_protection`: one WARN; write/config channel not available in current tool surface.

## Security gate status

Green now:

- reviewed APP RPC source promotion;
- live exact-SHA runtime smoke;
- caller-zero source migration for promoted target callers;
- live gateway health and anonymous fail-closed boundary;
- five target server-wrapper RPC parity and rollback transaction evidence;
- exact retirement SQL/rollback prepared for migrated legacy RPCs.

Still fail-closed:

- authenticated HTTP E2E using a safe dedicated identity;
- full write-path cleanup/rollback proof through HTTP;
- selective legacy EXECUTE retirement;
- post-retirement E2E and advisor refresh;
- disposition of remaining SECURITY DEFINER warnings.

Canonical human exception for creating/using a new dedicated PROD test identity: `HUMAN_REQUIRED: HIGH_RISK` unless an already-authorized test principal is discovered.

## Recovery

- Existing workflow `.github/workflows/prod-rollback-rehearsal.yml` is non-mutating and accepts an exact `target_sha`, builds with PROD configuration, verifies PROD-only backend binding, prepares a rollback artifact, and does not publish.
- Previous deployed source `c7a15cff9a387f1f142c8eeb06fd83a799e85a61` still resolves as an immutable Git commit and is therefore a real source rollback candidate.
- No historical `workflow_dispatch` run exists in the repository at this cut, so a successful old-SHA rollback rehearsal is not claimed.
- Provider-level Supabase isolated restore remains open; no unapproved paid branch/project is created.

## FinOps evidence refresh

Notion workspace source `MATRIZ REAL COMPLETA DE COSTES FÉNIX` contains a current reference row for `Notion`:

- `Importe base €`: 20 (field label is EUR, but source note explicitly says the official reference is **20 USD/member/month** for Business as of 2026-08-26);
- status: `En progreso`;
- note: actual cost depends on paid member count and monthly/annual billing; real invoice in EUR is still required.

This conflicts with older email evidence that referenced Plus/trial history; therefore it is not used as an exact current invoice amount.

Google Cloud: current connected-source search confirms payment-problem/suspension notices for `fenix-trading-lab`, but no authoritative exact monthly amount or zero-cost proof was found. Do not estimate.

## Promotion consequence

APP source promotion is complete, but global CEREBRO PROD candidate remains fail-closed until SECURITY, RECOVERY, OBSERVABILITY and FINOPS gates are evidenced. Final promotion remains human-gated.