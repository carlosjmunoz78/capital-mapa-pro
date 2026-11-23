-- ZEUS CP86: isolated additive journal in existing FACT-001 LAB D1.
-- Do not modify, delete, or retry FACT job rows. Rollback the Worker version;
-- retain the audit journal unless a separate authorized cleanup is approved.
CREATE TABLE IF NOT EXISTS zeus_fact_p5_health_v1 (
  receipt_id TEXT PRIMARY KEY NOT NULL CHECK(receipt_id GLOB 'ZEUS-P5-????????-fenix-capital-LAB'),
  company_id TEXT NOT NULL CHECK(company_id='fenix-capital'),
  engine_id TEXT NOT NULL CHECK(engine_id='FACT-001'),
  environment TEXT NOT NULL CHECK(environment='LAB'),
  version TEXT NOT NULL CHECK(version='1.0.0'),
  day_key TEXT NOT NULL UNIQUE CHECK(length(day_key)=8),
  request_id TEXT NOT NULL CHECK(request_id GLOB 'FACT001-P5-*'),
  state TEXT NOT NULL CHECK(state IN ('GREEN','BLOCKED')),
  code TEXT NOT NULL CHECK(code IN (
    'GREEN','AUTOMATION_DRIFT','DAILY_JOB_MISSING_OR_SCOPE_INVALID',
    'DAILY_JOB_NOT_COMPLETED','RECEIPT_OR_COST_INVALID','NEW_RECONCILE'
  )),
  observed_at_ms INTEGER NOT NULL CHECK(observed_at_ms>0),
  fingerprint_sha256 TEXT NOT NULL CHECK(length(fingerprint_sha256)=64),
  source TEXT NOT NULL CHECK(source='ZEUS_P5_SHARED_RUNTIME')
);
