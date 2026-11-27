# Separate production release authority — candidate only

Base: 15530d0d0f40c46bf28e78083edafc22396e178f. Existing CP189 review and 12 gates unchanged. No workflow deployment job, no runtime activation, no new credentials, no changes to existing services. The new entrypoint calls the real review, verifies a distinct authority signature bound to exact candidate, evidence package, target and hold-resolution digest, then atomically reserves one release in an independently provisioned PROD ledger. A reservation is not a deployment.

Trusted runtime must provision independent identity and key, exact allowed target, real hold-resolution evidence, active holds and durable ledger, verify anti-rollback/fencing across restore, and connect the executor to reservation expiry, digest and one-time execution. Never accept trust configuration from callers. Never clear a platform restriction by changing code or routing. Existing HOLDs remain in force. No keys or live approvals are included.

Ledger provisioning contract: release_ledger_scope contains exactly one row PROD. release_reservations requires primary key release_id and UNIQUE(target,company_id,engine_id,commit_sha,artifact_sha256), with non-null columns as used in tests. No automatic create, reset or retry on ambiguous results. A production integration must verify this schema, persistence and fencing before use. Test fixture databases and signatures are not production evidence.

Tests use the existing workflow and test file. Rollback: keep candidate branch unmerged; no live changes to roll back. Actual deployment authorization requires all external and internal gates, trusted runtime and independent release approval. Cost of this code change: no new subscription; CI subject to existing quotas.
