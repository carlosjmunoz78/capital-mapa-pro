# TAX-001 · Rollback / Rebuild · LAB

## Scope
TAX-001 V0 is decision-support only and `prod_enabled=false`.

## Rollback
1. Disable TAX-001 routing in LAB.
2. Revert the TAX-001 capability commit/branch to the previous known-good revision.
3. Preserve the fiscal knowledge corpus and evidence artifacts; do not delete historical versions.
4. Re-run repository unit tests, runtime rehearsal and release rollback rehearsal.
5. Record rollback evidence before re-enabling routing.

## Rebuild
1. Recreate the scaffold from FACT-001 using canonical engine ID `TAX-001`.
2. Restore the manifest and decision-support contract from Git history.
3. Rebind only evidence/currentness artifacts that pass the canonical fiscal gates.
4. Re-run contract, policy, knowledge and tribunal gates.
5. Keep PROD disabled until a separate promotion decision is evidenced.

## Safety
No App/CRM/PROD mutation is part of this V0. External filing, payment, signature, amendment and appeal are fail-closed.
