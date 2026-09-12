# CEREBRO OS · Make TEST unique closure · 2026-09-12

Purpose: exact unique-by-`scenario_id` closure of Make folder `10 · FENIX · TEST` (`520862`). This supersedes the earlier partial arithmetic in this same file.

## Live totals — corrected from direct Make state

- Folder total: **120** scenarios.
- Active scenarios: **2**.
  - `9555725` — `FÉNIX · CORE · Cerebro · Señal a Idea, Embudo, Evaluación y Laboratorio · V2.2`.
  - `9538231` — `FÉNIX · PROD · SEO · GA4 páginas 30d · Vigilancia semanal · V2`.
- Make `error` scenarios: **1**.
  - `9529670` — historical TEST Notion/Facebook/Assets validation, zero incomplete executions.
- Therefore live inactive rows: **117**.

Important correction: earlier audit text said active TEST = 0. Direct `status=active` enumeration disproved that assumption. The live Make state is authoritative and the audit is corrected here instead of preserving a false green.

## Active scenario evidence

### `9538231` — GA4 pages 30d weekly surveillance
- Active scheduled every 604800 seconds.
- Single GA4 report module.
- GA4 connection `14524247` is `ok` and explicitly read-only by label.
- Successful automatic executions include 2026-08-18, 2026-08-19 and 2026-09-07; recent successful runs consume 1 operation / 1 credit each.
- Architectural decision: **KEEP_ACTIVE / WRAP_WITH_CEREBRO**. Make remains a low-cost SaaS collection edge; canonical history/analysis belongs to CEREBRO.

### `9555725` — signal → idea → funnel → evaluation → laboratory
- Active on-demand subscenario.
- Flow: subscenario input → Data Store dedupe → Notion writes → Data Store completion.
- Description explicitly states TEST-protected and no PROD publication.
- Notion connection `14347958` status `ok`.
- Two successful executions on 2026-09-07; one used 6 operations / 6 credits and one used 1 operation / 1 credit.
- Architectural decision: **MIGRATE_TO_RUNTIME after parity**. Signal routing/dedupe/Idea→Matriz→Evaluación→Laboratorio are CEREBRO domain logic; Make/Notion may remain temporary edge/source while OLD vs NEW parity is proven.

## Exact inactive coverage

The connector has a hard cap of 25 rows and no pagination. The inactive set is nevertheless closed exactly by three non-overlapping creation-order regions:

- **25 oldest inactive**: `9522340` through `9538330`, ending at `2026-07-17T10:04:52.565Z`.
- **67 unique middle inactive IDs**, enumerated below.
- **25 newest inactive**: beginning at `9678708` (`2026-08-18T18:46:10.490Z`) and ending at `9721586`.

Arithmetic: `25 + 67 + 25 = 117` inactive scenarios.

## 67 middle inactive IDs

### SEO / GSC / technical web — 14
`9539054`, `9539106`, `9540445`, `9542046`, `9550772`, `9553491`, `9553521`, `9555536`, `9557377`, `9557396`, `9557586`, `9557591`, `9557597`, `9557608`.

### RADAR own-social signals — 5
`9595955`, `9597297`, `9597307`, `9597332`, `9597372`.

### Carrusel — 16
`9678069`, `9678094`, `9678096`, `9678171`, `9678213`, `9678216`, `9678317`, `9678369`, `9678390`, `9678407`, `9678478`, `9678538`, `9678542`, `9678611`, `9678612`, `9678643`.

### Imagen — 14
`9678067`, `9678167`, `9678205`, `9678212`, `9678273`, `9678303`, `9678500`, `9678524`, `9678541`, `9678595`, `9678607`, `9678634`, `9678636`, `9678704`.

### Texto — 6
`9678165`, `9678204`, `9678499`, `9678523`, `9678592`, `9678632`.

### Reel — 2
`9678070`, `9678217`.

### Generic publication/preflight controls — 2
`9678050`, `9678180`.

### Notion readers — 2
`9538346`, `9538380`.

### WordPress TEST utility — 1
`9540674`.

### CEREBRO operational/intelligence utilities — 3
`9555634`, `9557354`, `9597883`.

### Embudo/evaluation utilities — 2
`9555520`, `9557594`.

Arithmetic: `14 + 5 + 16 + 14 + 6 + 2 + 2 + 2 + 1 + 3 + 2 = 67`.

## Final folder closure

- 117 inactive unique IDs.
- 2 active unique IDs.
- 1 error unique ID.

Total: **120 / 120 scenarios uniquely accounted for**.

## Safety / architectural status

`TEST 120/120` is now **GREEN for inventory/classification**, not permission to activate legacy mutators. All surfaced inactive scenarios remain inactive; newly audited rows report `incompleteExecutions=0`. `DEPRECATED`, `NO USAR`, staging, dry-run, gate and publisher scenarios remain quarantined unless dependency/parity gates explicitly promote or retire them.

The two active rows are legitimate live exceptions to the previous assumption: GA4 weekly collection is low-cost/read-only edge collection; the CEREBRO signal pipeline is non-publishing but should migrate to runtime after parity.
