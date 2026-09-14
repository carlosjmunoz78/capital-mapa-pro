# CEREBRO Recovery — provider DB restore gate — 2026-09-14

## ESTADO

State: **PARCIAL / APP_SOURCE_ROLLBACK_GREEN / PROVIDER_DB_RESTORE_MONEY_LIMIT**

## LIVE READ-ONLY AUDIT

Supabase project:
- project: `fenix-capital-prod`
- ref: `cluhljgonannaafpmblx`
- region: `eu-west-2`
- status at audit time: `ACTIVE_HEALTHY`
- organization plan: `pro`

Branch inventory at audit time contains only the default `main` branch. There is no existing isolated development/restore branch available as a zero-additional-cost target that has been proven safe for a provider-level restore drill.

## WHAT IS ALREADY GREEN

App source-release rollback has already been rehearsed non-destructively:
- previous source candidate built successfully;
- canonical PROD binding validated;
- static rollback snapshot produced as an artifact;
- nothing was published during the rehearsal.

See `APP_PROD_ROLLBACK_REHEARSAL_C7A15C_2026-09-14.md`.

## BLOCKER

A provider-level database restore must **not** be tested against PROD.

To close this dimension safely, CEREBRO needs an isolated restore target plus restore → integrity → smoke → cleanup evidence. No such isolated target currently exists in the project branch inventory.

Creating a new paid Supabase project/branch or enabling a paid restore path is a `MONEY_LIMIT` decision and must not be performed without explicit cost confirmation.

## CURRENT DECISION

- Do not restore onto PROD.
- Do not create a paid branch/project automatically.
- Keep source rollback GREEN.
- Keep provider DB restore **fail-closed / HUMAN_REQUIRED(MONEY_LIMIT)** until an approved isolated target exists.

This blocker is external/economic rather than an unimplemented source-recovery mechanism.
