# Professional Advisory · Dependency Map

Cutoff: 2026-09-15

## Runtime path

`CEREBRO Gateway -> advisory.gateway.AdvisoryGatewayRequest -> advisory.router.route_case -> advisory.runtime.execute_case -> advisory.capabilities.CAPABILITY_REGISTRY -> injected domain handlers -> advisory.coordinator.coordinate -> AdvisoryGatewayResponse`

The orchestrator component is `PROFESSIONAL_ADVISORY`; it is not a new canonical engine. `engine_id` always identifies a canonical underlying engine. Multi-company identity is carried by `company_id`; trace identity by `case_id` and `correlation_id`; environment/version remain explicit.

## Case and knowledge path

`Gateway request -> AdvisoryCase -> CaseStore(company_id, case_id) -> SourceRecord/source policy -> DomainOpinion -> ProfessionalAdvisoryOutput`

Source classes remain separated as `STABLE_KNOWLEDGE`, `LIVE_SOURCE`, `INTERNAL_DOCUMENT`, and `CASE_FACT`. The current physical source lock records 12/12 domains bound and zero missing artifacts.

## Integration path

`Professional output / decision -> IntegrationOutbox -> target adapter injected by caller`

Targets: CRM, Company Registry, Venture Factory, Contracts, HR, Finance, Operations, and Extension. No external write occurs without an explicitly injected adapter. Events carry `correlation_id`, `company_id`, `case_id`, `event_id`, and `idempotency_key`; retries are bounded and idempotent.

## Observability and recovery

`ExecutionTelemetry -> TelemetryCollector -> structured logs + metrics`

Tracked: executions, errors, error rate, latency, confidence, audit refs, correlation ID, and measured cost.

`CaseSnapshot(s) -> AdvisoryBackupBundle(SHA-256) -> rebuild_case_store()`

Rollback remains an explicit `rollback_ref`; release rollback is additionally rehearsed by the repository CI workflow.

## Isolation boundaries

PREPROD is hosted in project `cerebro-forge`, region `europe-southwest1`, service `cerebro-advisory-preprod`. External writes, App/CRM access, PROD credentials, and customer data remain disabled by the PREPROD contract. Trading is outside this dependency graph and remains isolated.

## Promotion boundaries

Current supported state: LAB green, PREPROD capability green, isolated PREPROD advisory-autonomy candidate green. `capability_green_global=false`, `autonomy_green=false`, `prod_enabled=false`. Global/customer-data/security/PROD promotion remains a separate gate.
