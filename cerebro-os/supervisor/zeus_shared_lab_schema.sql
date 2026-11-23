-- CP86 LAB · ADDITIVE ONLY. Never mutate or replay existing FACT jobs.
CREATE TABLE IF NOT EXISTS cerebro_zeus_supervisor_events_lab_v1 (
  event_id TEXT PRIMARY KEY NOT NULL,
  company_id TEXT NOT NULL,
  engine_id TEXT NOT NULL,
  environment TEXT NOT NULL CHECK(environment='LAB'),
  version TEXT NOT NULL,
  check_id TEXT NOT NULL,
  day_key TEXT NOT NULL,
  request_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('HEALTHY','INCIDENT')),
  incident_code TEXT NOT NULL,
  observed_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zeus_supervisor_scope_day_lab_v1
 ON cerebro_zeus_supervisor_events_lab_v1(company_id,engine_id,environment,version,day_key);
