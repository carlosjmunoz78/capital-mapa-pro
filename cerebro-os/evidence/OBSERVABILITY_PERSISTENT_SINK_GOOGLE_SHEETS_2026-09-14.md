# CEREBRO Observability — persistent zero-cost sink proof — 2026-09-14

## HECHO

A dedicated persistent Google Sheets sink was created without adding a new paid subscription:

- File: `CEREBRO_PROD_OBSERVABILITY_V1`
- Spreadsheet id: `1y3SAovlDpcK9TxZB3Gm-0nYUpY9AZyH-W0y9e1u8kRw`
- Sheet: `Sheet1`
- Scope contract columns:
  - `timestamp`
  - `company_id`
  - `engine_id`
  - `environment`
  - `version`
  - `kind`
  - `run_id`
  - `status`
  - `message`
  - `payload_json`

A dedicated Make on-demand bridge was created:

- Scenario id: `9804649`
- Name: `CEREBRO · OBSERVABILITY · Persistent sink · LAB V1`
- Trigger: on-demand subscenario input contract
- Sink: Google Sheets `addRow`
- Connection: existing authorized Google connection

## LOOP / ERROR CORRECTION

First execution failed closed because `valueInputOption` was missing. The module was corrected with explicit `USER_ENTERED` and `INSERT_ROWS`.

A second execution completed but the first column mapper shape (`A`..`J`) produced an empty inserted row. The mapping was corrected to the connector's positional keys (`0`..`9`).

Final controlled synthetic smoke:

- execution id: `4c9be20f08e54126b4a8a3ab9bb9fd09`
- environment: `LAB`
- company_id: `FENIX_CAPITAL`
- engine_id: `OBSERVABILITY_TEST`
- run_id: `obs-sink-smoke-20260914-r3`
- status: `GREEN`
- result: success, row 2

Independent Google Sheets read-back confirmed all ten fields persisted in row 2 with the expected values.

## ESTADO

Persistent zero-cost auxiliary storage contract: **GREEN LAB / READY FOR PARALLEL WIRING**.

This does **not** claim that every PROD engine is already mirrored. Existing PROD observability remains untouched. The next safe gate is parallel wiring by engine/family with OLD vs NEW comparison and rollback, never replacement-in-place.

## SAFETY

- No existing Make datastore was repurposed.
- No Supabase transactional table was burdened with this auxiliary sink.
- No secret was written to the smoke row.
- The smoke row is explicitly synthetic and LAB-scoped.
- No existing PROD logging path was deleted or changed.
