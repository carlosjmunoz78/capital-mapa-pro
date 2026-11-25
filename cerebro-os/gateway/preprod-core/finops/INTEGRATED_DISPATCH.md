# Integrated FinOps overlay — candidate only
Original 1.1.0 artifact unchanged. Build from exact 22-file base and pinned manifest.
The overlay changes only dispatcher entrypoint and adds 3 modules (25 files).
Protocol remains 1.1.0; artifact revision distinguishes the candidate.
Private Durable Object CoreFinOpsLedger in dispatcher script, EU jurisdiction, one object per account.
Required bindings: CORE_FINOPS_LEDGER (new isolated SQLite DO class, not existing IAM ledger), CORE_FINOPS_ENABLED, CORE_FINOPS_ACCOUNT, CORE_FINOPS_PLAN (administrative JSON), CORE_FINOPS_DAILY_LIMIT (1..8).
No public route, no cron, no new subscription. Do not provision until reviewed and Free limits verified.
Plan observation expires after 24h; unknown/stale fails closed, no synthetic observation in production.
DEFER uses one native durable Workflow sleepUntil at next UTC day, then revalidates through the same ledger before sending. If quota or trusted plan still unavailable, returns DEFER/HOLD; no unbounded wake loop. Further queue integration remains pending. HOLD requires reconciliation by original ID, no retry.
Old dispatcher untouched, rollback to exact existing version; retained reservations must never be reset.
Test provider workflow emulation with actual Ed25519 machine/supervisor signatures, SQLite, compiled entrypoint; not physical cloud certification.
No owner identity changes or bypass of prior security HOLD.
