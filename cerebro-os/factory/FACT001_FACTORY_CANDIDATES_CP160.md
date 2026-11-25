# CP160 · FACT candidate registry (LAB only)

Additive metadata-only table. Not an IAM issuer, runtime registry or automatic provisioner.
Only scope fenix/LAB; never aliases fenix-capital. Existing administrative registry untouched.
Register verified repository evidence using exact source commit and evidence blob.
All authority, execution, production and media flags constrained to zero.
Do not bind operational workers to this table or use as grant source.
Preflight: verify absent table, D1 bookmark, prior legacy schema/rows hashes and exact source blobs.
Scoped rollback: mark matching candidate RETIRED, matching complete identity/source/evidence; retain audit.
Do not restore entire D1 to undo this additive change. Local rollback and backup rehearsal only.
Remote operation requires CI success and independent readback of new row and unchanged legacy.
