# CEREBRO OS · Make scenario audit · 2026-09-12

## Scope
Evidence-first inventory of Make team `1927480`. No scenario was activated or deleted to manufacture green evidence. PROD mutators remain fail-closed/inactive unless already intentionally active. Raw credentials are not recorded.

## HECHO / GREEN
- Folder `00 · FENIX · AUDITORÍA Y LEGACY` fully inventoried: 9/9 scenarios accounted for. Four scenarios are in Make `error` state but explicitly historical/invalid/NO USAR or documented failed probes; the remaining five are inactive historical/calibration/legacy flows. None is active and none has incomplete executions.
- Folder `40 · FENIX · PREVENTIVO Y RECUPERACIÓN` fully inventoried: 2/2 scenarios inactive, no incomplete executions.
- Folder `50 · FENIX · ALERTAS Y MONITORIZACIÓN` fully inventoried: 8/8 scenarios inactive, no incomplete executions. Some descriptions still say historically ACTIVO; live state is authoritative and currently inactive.
- Folder `20 · FENIX · PROD` fully inventoried: 25/25 scenarios accounted for. Exactly two are active: `9597710` GSC 30d → Inventario Notion and `9550706` Search Console vigilancia semanal. Both use connection `14438259` with status `ok`; `9597710` also uses Notion connection `14435131` with status `ok`.
- Active PROD evidence: `9597710` has successful automatic executions on 2026-08-19, 2026-08-26, 2026-09-02 and 2026-09-09; latest execution performed 147 operations successfully. `9550706` has a successful automatic execution on 2026-09-07.
- All publishing/mutating Facebook, Instagram, LinkedIn and YouTube scenarios in the PROD folder are currently inactive. Several descriptions explicitly require go-live authorization; this state is preserved.
- The two one-shot Lucena publication scenarios are inactive.
- PRE-PROD inventory remains 3/3 inactive. The two WordPress webhooks are fail-closed with sentinel `__DISABLED_LEGACY_PREPROD__`; queues are empty. Google bridge PRE-PROD remains inactive/read-only with healthy GSC and GA4 connections.
- `social-lead-ingest` scenario `9768402` configuration remains on Make-managed API-key authentication with no literal `x-fenix-key` in its mapper. Runtime verification remains separately pending because a synthetic run would mutate APP/CRM PROD.
- Folder `30 · FENIX · CORE E INTELIGENCIA` active subset is fully inventoried: 8 active scenarios, all with `incompleteExecutions=0`.
- Active on-demand Instagram analytics/reconciliation scenarios `9534096` and `9534088` use Facebook/Instagram connection `14428711` and Notion `14435131`, both `ok`; their flows are analytics/reconciliation, not publication.
- Active on-demand LinkedIn analytics/reconciliation scenarios `9523007` and `9405249` use LinkedIn `14435718` and Notion `14435131`, both `ok`; their flows read post/statistics data and persist evidence, not publish.
- Active scheduled CORE reconciliation `9527242` is deterministic datastore-only. All 25 returned runs from 2026-09-10 through 2026-09-12 are `success`; latest run on 2026-09-12 completed 5 operations successfully.
- Active scheduled watchdog `9705138` uses Notion connection `14435131` with status `ok`. All 25 returned recent runs are `success`; latest run on 2026-09-12 completed 2 operations successfully.
- Active MASTER Facebook control/analytics `9533690` uses Notion `14435131` and Facebook `14428711`, both `ok`, and contains no publication module. Its automatic runs on 2026-09-07 through 2026-09-12 are all `success`; latest run completed 12 operations successfully.
- Folder `10 · FENIX · TEST`: live error-state partition is now fully enumerated. Exactly one TEST scenario is in Make `error` state: `9529670` (`FENIX · TEST · Notion · Validación contrato Facebook y Assets · V1`), inactive, zero incomplete executions. This is not an active production incident.
- TEST alphabetical low partition inspected: first 25 inactive scenarios are dominated by `DEPRECATED · NO USAR` Facebook/Instagram gate, dry-run, staging and fixture flows. They are explicitly non-PROD or fail-closed and have zero incomplete executions. Mutating historical publishers remain inactive.
- TEST alphabetical high partition inspected: latest-name partition includes Lucena no-run/scheduled verification, temporary Drive→WordPress asset transport, readback fixtures, GSC/SEO diagnostics, radar collectors and historical validation flows. All returned rows are inactive with zero incomplete executions.
- TEST Facebook partition inspected: returned inactive set contains deprecated gates/staging plus historical analytics/diagnostics and current TEST preflight/publicador validation. No returned Facebook TEST scenario is active; hard-arm/publicador scenarios remain intentionally inactive.

## GREEN_QUARANTINED
The following classes are intentionally green-by-quarantine rather than green-by-execution:
- Historical scenarios explicitly marked `NO USAR`, `DEPRECATED`, `LEGACY`, failed audit/calibration probes, and replaced versions.
- Inactive TEST/TEMP scenarios that can mutate WordPress, upload media, generate assets or publish externally.
- Inactive PROD publishers awaiting explicit go-live/promotion evidence.

A quarantined scenario must not be reactivated merely to clear an audit state. Reactivation requires dependency review, current connection verification, policy gate, idempotency/rollback evidence and an explicit promotion path.

## PARCIAL / remaining
- Folder `10 · FENIX · TEST` contains 120 scenarios. The error-state subset is fully enumerated and multiple alphabetical/category partitions are now evidenced, but full 120/120 unique-row classification remains in progress because the Make connector has no paging and returns at most 25 rows per list operation.
- Folder `30 · FENIX · CORE E INTELIGENCIA` contains 62 scenarios. Its active 8/8 subset is fully audited with connection/runtime evidence where scheduled; inactive historical scenarios remain to be partitioned and classified.
- `social-lead-ingest` runtime authentication proof remains pending a real non-duplicate business event; no synthetic PROD mutation will be generated solely for evidence.

## Promotion / preservation rule
CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR.
No inactive historical scenario is deleted, activated or rewritten without dependency map, preserved contract, rollback path and evidence. Error status in an explicitly archived/NO USAR scenario is not treated as a production incident; its safe state is inactive/quarantined with replacement or failure reason documented.
