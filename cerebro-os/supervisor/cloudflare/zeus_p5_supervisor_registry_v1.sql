-- CP87: append-only daily projection into a scoped Engine Registry read model.
-- Does not rewrite canonical engine registry, FACT P5 jobs or CP86 health receipt.
CREATE TABLE IF NOT EXISTS zeus_fact_p5_registry_projection_v1 (
 snapshot_id TEXT PRIMARY KEY NOT NULL CHECK(snapshot_id GLOB 'GOV-001:FACT-001:P5:LAB:????????'),
 company_id TEXT NOT NULL CHECK(company_id='fenix-capital'),
 engine_id TEXT NOT NULL CHECK(engine_id='FACT-001'),
 environment TEXT NOT NULL CHECK(environment='LAB'),
 version TEXT NOT NULL CHECK(version='1.0.0'),
 day_key TEXT NOT NULL UNIQUE CHECK(length(day_key)=8),
 receipt_id TEXT NOT NULL UNIQUE REFERENCES zeus_fact_p5_health_v1(receipt_id),
 request_id TEXT NOT NULL CHECK(request_id GLOB 'FACT001-P5-*'),
 registry_state TEXT NOT NULL CHECK(registry_state IN ('LAB_GREEN','BLOCKED')),
 health_code TEXT NOT NULL CHECK(health_code IN (
 'GREEN','AUTOMATION_DRIFT','DAILY_JOB_MISSING_OR_SCOPE_INVALID',
 'DAILY_JOB_NOT_COMPLETED','RECEIPT_OR_COST_INVALID','NEW_RECONCILE')),
 supervisor_action TEXT NOT NULL CHECK(supervisor_action IN ('NONE','SUPERVISOR_REVIEW')),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 created_at_ms INTEGER NOT NULL CHECK(created_at_ms>0),
 promotion_allowed INTEGER NOT NULL DEFAULT 0 CHECK(promotion_allowed=0)
);
CREATE TABLE IF NOT EXISTS zeus_fact_p5_exceptions_v1 (
 incident_id TEXT PRIMARY KEY NOT NULL,
 snapshot_id TEXT NOT NULL REFERENCES zeus_fact_p5_registry_projection_v1(snapshot_id),
 company_id TEXT NOT NULL CHECK(company_id='fenix-capital'),
 engine_id TEXT NOT NULL CHECK(engine_id='FACT-001'),
 environment TEXT NOT NULL CHECK(environment='LAB'),
 version TEXT NOT NULL CHECK(version='1.0.0'),
 day_key TEXT NOT NULL CHECK(length(day_key)=8),
 code TEXT NOT NULL CHECK(code IN (
 'AUTOMATION_DRIFT','DAILY_JOB_MISSING_OR_SCOPE_INVALID',
 'DAILY_JOB_NOT_COMPLETED','RECEIPT_OR_COST_INVALID','NEW_RECONCILE')),
 exception_class TEXT CHECK(exception_class IN (
 'LEGAL_REQUIRED','SIGNATURE_REQUIRED','LOW_CONFIDENCE','HIGH_RISK',
 'POLICY_CONFLICT','SECURITY_INCIDENT','MONEY_LIMIT','CUSTOMER_HUMAN_REQUEST')),
 human_required INTEGER NOT NULL CHECK(human_required IN (0,1)),
 source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
 created_at_ms INTEGER NOT NULL CHECK(created_at_ms>0),
 incident_state TEXT NOT NULL DEFAULT 'OPEN' CHECK(incident_state='OPEN'),
 UNIQUE(snapshot_id,code)
);
