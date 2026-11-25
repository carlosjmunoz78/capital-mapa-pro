# CP189 persistent receipt store candidate — 2026-11-25

Additive adapter, no release authority, no changes to active runtime. The existing
signed receipt verifier and fail-closed gate read a single consistent SQLite snapshot.
The trusted runtime, not the requester, must supply the absolute DB path, pinned
issuer keys, clock and policy. No private keys, no signing, no DB creation, no writes.

Store contract (provisioned separately by authorized independent evidence producers):
```sql
CREATE TABLE promotion_receipts(
 gate TEXT NOT NULL, evidence_id TEXT NOT NULL,
 payload BLOB NOT NULL, envelope TEXT NOT NULL,
 PRIMARY KEY(gate,evidence_id)
);
```
Envelope is the existing CP189 signed JSON format; payload is the exact bytes hashed
by the signer. The adapter rejects missing, malformed, duplicate, oversized, expired,
cross-candidate and signature-invalid evidence. Gate booleans are derived from
readback, not caller flags. A positive decision remains REVIEW_CANDIDATE with
deployment_authorized=false. No LAB receipt can certify PROD.

Tests use ephemeral synthetic keys and an actual local SQLite file; they do not
certify production or constitute independent real evidence. Production issuance,
trusted runtime deployment, final FinOps and release authority remain HOLD.
Rollback: revert only these additive files and optional CI path change.
