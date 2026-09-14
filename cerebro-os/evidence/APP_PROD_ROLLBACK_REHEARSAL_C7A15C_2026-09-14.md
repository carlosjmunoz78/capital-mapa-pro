# APP PROD rollback rehearsal · previous live source · 2026-09-14

## HECHO

A non-destructive App recovery rehearsal was executed against the previous known PROD source commit:

- rollback candidate: `c7a15cff9a387f1f142c8eeb06fd83a799e85a61`
- isolated branch: `cerebro-prod-rollback-rehearsal-c7a15c-20260914`
- branch setup commit: `0bf3dc1f1a6f77045efc917808af80e13c1f6ba1`
- workflow: `CEREBRO PROD Rollback c7a15c Rehearsal`
- run: `34808719859`
- result: SUCCESS

Successful gates:

- exact previous PROD SHA checkout verified;
- reproducible dependencies installed;
- previous PROD source built against canonical current PROD binding;
- legacy PREPROD backend URL absent from rollback artifact;
- canonical PROD backend URL present;
- rollback static snapshot prepared;
- `CNAME=app.fenixcapital.es` validated;
- rollback candidate SHA embedded and validated;
- artifact uploaded only; **nothing was published**.

Artifact evidence:

- artifact id: `10333274904`
- name: `fenix-prod-rollback-c7a15c-rehearsal`
- digest: `sha256:1d461022a00576a41acac8857af809aeff7666e0b4cdbd541f6fc67f6e4e787a`
- retention expiry: `2026-09-21T05:11:50Z`

## CONSEQUENCE

`real_release_or_provider_rollback_target_proven` is now GREEN for the App source-release rollback dimension. This does **not** prove a Supabase provider-level database restore. Provider restore remains fail-closed until an isolated non-PROD restore target exists and restore/integrity/smoke/cleanup are executed without unapproved cost.

No APP PROD deployment, no PREPROD reactivation and no Supabase mutation occurred in this rehearsal.