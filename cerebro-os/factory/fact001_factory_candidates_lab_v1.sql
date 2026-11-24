CREATE TABLE fact001_factory_candidates_lab_v1 (
  company_id TEXT NOT NULL CHECK(company_id='fenix'),
  engine_id TEXT NOT NULL CHECK(length(engine_id) BETWEEN 3 AND 64 AND engine_id NOT GLOB '*[^A-Z0-9-]*' AND engine_id GLOB '*[A-Z]*' AND engine_id NOT LIKE '-%' AND engine_id NOT LIKE '%-' AND engine_id NOT LIKE '%--%'),
  environment TEXT NOT NULL CHECK(environment='LAB'),
  version TEXT NOT NULL CHECK(length(version) BETWEEN 5 AND 32),
  source_commit TEXT NOT NULL CHECK(length(source_commit)=40 AND source_commit NOT GLOB '*[^0-9a-f]*'),
  evidence_blob TEXT NOT NULL CHECK(length(evidence_blob)=40 AND evidence_blob NOT GLOB '*[^0-9a-f]*'),
  artifact_count INTEGER NOT NULL CHECK(artifact_count>0),
  state TEXT NOT NULL DEFAULT 'CANDIDATE_REGISTERED' CHECK(state IN ('CANDIDATE_REGISTERED','RETIRED')),
  registration_method TEXT NOT NULL CHECK(registration_method='OPERATOR_VERIFIED_FACTORY_ARTIFACTS'),
  authority_verified INTEGER NOT NULL DEFAULT 0 CHECK(authority_verified=0),
  execution_granted INTEGER NOT NULL DEFAULT 0 CHECK(execution_granted=0),
  production_authorized INTEGER NOT NULL DEFAULT 0 CHECK(production_authorized=0),
  media_dispatch_enabled INTEGER NOT NULL DEFAULT 0 CHECK(media_dispatch_enabled=0),
  cost_ceiling_eur INTEGER NOT NULL DEFAULT 0 CHECK(cost_ceiling_eur=0),
  PRIMARY KEY(company_id,engine_id,environment,version)
);
