# Professional Advisory · Runbook

Cutoff: 2026-09-15

## Start / verify

1. Verify base branch `cerebro-engine-factory-v0` and current physical commit before making changes.
2. Run repository unit tests and the Engine Factory workflow.
3. For PREPROD promotion, require the FORGE workflow to deploy only to `cerebro-forge/europe-southwest1/cerebro-advisory-preprod`.
4. Confirm isolation evidence: external writes disabled, App/CRM access disabled, PROD credentials disabled, customer data disabled.

## Gateway execution

Construct `AdvisoryGatewayRequest` with `company_id`, `component_id=PROFESSIONAL_ADVISORY`, canonical `engine_id`, `environment`, `version`, `case_id`, `correlation_id`, `actor`, `context`, `permissions`, `requested_service`, `territory`, and `facts`. Permission `advisory:execute` is mandatory. Unknown engines, incompatible engine/domain routing, missing permission, or unroutable cases fail closed.

## Sources

Before professional output, assess sources by type, jurisdiction, validity window, `checked_at`, and confidence. Current/live source can be mandatory. Missing or obsolete current evidence produces `LOW_CONFIDENCE`. Per-opinion provenance must match accepted source IDs.

## Human exception

Only the canonical eight codes are valid: `LEGAL_REQUIRED`, `SIGNATURE_REQUIRED`, `LOW_CONFIDENCE`, `HIGH_RISK`, `POLICY_CONFLICT`, `SECURITY_INCIDENT`, `MONEY_LIMIT`, `CUSTOMER_HUMAN_REQUEST`.

## Integrations

Enqueue integration events in `IntegrationOutbox`. Do not perform an external write unless the caller explicitly supplies a target adapter. Reuse the same `idempotency_key` on retry. Missing adapter fails closed. Adapter failures retry up to the configured maximum and then block.

## Observability

Emit `ExecutionTelemetry` with correlation/company/case/engine/environment/status, latency, confidence, audit refs, errors, and cost. Health/readiness is deterministic and zero-cost. Cost must be measured; the default target remains 0 EUR additional recurring cost.

## Backup / rebuild

Create `AdvisoryBackupBundle` from case snapshots before risky changes. Record the source version and `rollback_ref`. Verify the SHA-256 digest. Rebuild with `rebuild_case_store(bundle)` and verify company/case isolation before reuse.

## Rollback

Code rollback: restore the last verified merge commit or release reference, then run the same CI and PREPROD verification path. Data rollback: rebuild from a verified backup bundle. Never roll back by deleting existing App/CRM/Supabase/Notion/WordPress assets.

## Current verified sequence before Block E merge

- Block A: PR #52 -> merge `6cab9289cfb3747a8779dda32d72bcca3e539f66` -> FORGE run `35010956034` (#15) success.
- Block B: PR #53 -> merge `ffeb04edfdf45e18521fa3e1ede6916730956694` -> FORGE run `35025072225` (#16) success.
- Block C: PR #54 -> merge `28b9dd92ad0634380169ff1e32f2f6c34af56d21` -> FORGE run `35025424337` (#17) success.
- Block D: PR #55 -> merge `eff999dbbd60adc44a1ea372fd947f4d6d867f96` -> FORGE run `35025812256` (#18) success.

## Current promotion state

PREPROD capability and isolated PREPROD advisory-autonomy candidate are green. Global capability/autonomy and PROD remain disabled until separately evidenced. App/CRM PROD remains untouched.
