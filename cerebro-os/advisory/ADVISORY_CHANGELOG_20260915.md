# Professional Advisory · Changelog · 2026-09-15

## Block A · Gateway and routing

Added versioned multi-company Gateway boundary, canonical engine validation, component/engine identity separation, explicit + automatic routing, fail-closed behavior, actor/context/permissions, versioned response, and Gateway -> Router -> runtime execution. PR #52 merged at `6cab9289cfb3747a8779dda32d72bcca3e539f66`; post-merge FORGE run #15 (`35010956034`) succeeded.

## Block B · Case context, sources, professional output

Added recoverable company-scoped CaseStore, defensive snapshot copies, source classes, jurisdiction/validity/confidence checks, current-source `LOW_CONFIDENCE`, normalized professional output, and strict source provenance. PR #53 merged at `ffeb04edfdf45e18521fa3e1ede6916730956694`; post-merge FORGE run #16 (`35025072225`) succeeded.

## Block C · Human exception, integrations, observability, recovery

Preserved the exact eight canonical HUMAN_REQUIRED codes. Added adapter-injected idempotent integration outbox with correlation/retry semantics, health/readiness, structured telemetry and metrics, measured cost, backup bundle SHA-256, rebuild and rollback references. PR #54 merged at `28b9dd92ad0634380169ff1e32f2f6c34af56d21`; post-merge FORGE run #17 (`35025424337`) succeeded.

## Block D · E2E, OLD vs NEW, tribunal

Added a 12-domain E2E suite over 3 representative cases, multidomain execution, multi-company isolation, existing-case recovery, obsolete-source/LOW_CONFIDENCE, HIGH_RISK, SIGNATURE_REQUIRED, LEGAL_REQUIRED, idempotency, and direct-runtime OLD vs Gateway NEW comparison. Added isolated PREPROD Advisory autonomy tribunal without global/PROD promotion. PR #55 merged at `eff999dbbd60adc44a1ea372fd947f4d6d867f96`; post-merge FORGE run #18 (`35025812256`) succeeded.

## Block E · Closure

Updates canonical status and documentation: dependency map, runbook, changelog, continuity state and closure tests. No new canonical engine ID is created because `PROFESSIONAL_ADVISORY` remains a capability orchestrator over existing engines. App/CRM/PROD are not modified. Additional subscription cost introduced: 0 EUR.
