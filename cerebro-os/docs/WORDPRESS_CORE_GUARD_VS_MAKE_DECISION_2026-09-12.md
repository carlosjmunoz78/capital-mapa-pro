# CEREBRO OS · WordPress Core Guard vs Make · decisión canónica · 2026-09-12

## Estado observado

### EXISTENTE
- Repositorio independiente `carlosjmunoz78/fenix-core-guard`.
- La rama `production` contiene el plugin completo: core, 42 archivos `src/`, REST, WordPress Abilities/MCP, CEREBRO/Notion, jobs, snapshots/restore, cache orchestration, updater, rollback y quality gates.
- Namespace REST documentado: `fenix-guard/v1`.
- Capabilities documentadas: `fenix_guard_view`, `fenix_guard_manage`, `fenix_guard_repair`.
- Rutas documentadas incluyen health, policy, incidents, URLs, integrity, history, snapshots, restore, alerts, rules, audits, jobs, cache, changes y logs.
- Contrato CEREBRO ↔ Core Guard incluye correlación, idempotencia, firma HMAC, fail-closed y acciones controladas.
- WordPress Abilities verificadas en código de rama `production`: `health`, `preprod-readiness`, `smoke-test`, `cerebro-status`, `capture-post-snapshot`, `purge-cache-url`, `restore-post-snapshot`.

### POR AUDITAR / INCONSISTENCIA
- La rama `main` está muy por detrás y sólo contiene un bootstrap mínimo que referencia `src/` sin incluir el árbol completo.
- La rama `production` contiene la implementación real completa, pero su documentación sigue marcando el build RC9 como PRE-PROD y exige gates separados para PROD.
- No se debe inferir que el plugin está operativo en PROD sólo por existir la rama `production`; falta evidencia LIVE actual de instalación/version/health/readiness/observer/rollback.
- Las Abilities actuales NO cubren todavía de forma explícita crear/duplicar páginas, actualizar contenido/SEO o subir media. Esos huecos impiden retirar Make por paridad hoy.

## Decisión arquitectónica

**WordPress debe ser plugin-first.**

Orden de preferencia:
1. Fénix Core Guard / WordPress Abilities / MCP.
2. REST/API propia del plugin.
3. CEREBRO Gateway + motores WordPress/SEO.
4. Make sólo como bridge externo cuando aporte un conector SaaS que Core Guard no cubra o como transición temporal.

Make no debe actuar como CMS paralelo ni duplicar capacidades ya cubiertas por Core Guard.

## Inventario Make WordPress · 17/17 escenarios nominales

Todos los escenarios devueltos por búsqueda `WordPress` están inactivos y con `incompleteExecutions=0`. Ninguno se activa para fabricar evidencia.

### GREEN_QUARANTINED · histórico / NO USAR
- `9551323` Compactación no canónica · NO USAR — getPost → updatePost. Conservar sólo trazabilidad.
- `9551189` Corrección REST fallida · NO USAR — makeApiCall x2. Conservar sólo incidente/trazabilidad.
- `9551187` Corrección visual fallida · NO USAR — getPost → updatePost. Conservar sólo incidente/trazabilidad.
- `9538815` WordPress → Notion V1 directa NO USAR — lectura WP → feeder → Notion sin antiduplicado integrado. Mantener archivado.
- `9694499` PRE-PROD CEREBRO SEO transport seguro — fail-closed, secreto legacy retirado. `RETIRE_CANDIDATE` sólo tras paridad/no-consumidores.
- `9694504` PRE-PROD CEREBRO SEO lectura segura — fail-closed, secreto legacy retirado. `RETIRE_CANDIDATE` sólo tras paridad/no-consumidores.
- `9681890` TEMP SEO corregir Córdoba PROD autorizado — getPost → updatePost. Mutador puntual; `REPLACE_AFTER_PARITY`.

### REPLACE_AFTER_PARITY · Core Guard/Gateway debe absorber la capacidad
- `9542046` Duplicar página WordPress como borrador — getPost → createPost. Falta ability segura equivalente.
- `9694471` CEREBRO SEO write-verify-rollback — create/get/update/get/update/get/delete. Útil como contrato OLD de prueba; no ejecutar. Debe convertirse en test de paridad del plugin, no runtime Make.
- `9540674` Corregir footer codificado — makeApiCall x2. Mutación WP determinista; debe gobernarla plugin/Gateway.
- `9556822` Reconstruir landing SEO en borrador — updatePost con title/slug/excerpt/content. Falta ability segura de contenido/SEO con snapshot y post-check.
- `9721363` Upload JPEG base64 → WordPress — createMediaItem. Falta ability media controlada con MIME/size/policy/idempotencia.

### MIGRATE_TO_PLUGIN_READ_API · lectura WordPress que no necesita Make a largo plazo
- `9557305` Inspección rutas REST WordPress — makeApiCall + aggregator. La inspección debe resolverse con Core Guard/REST/MCP.
- `9773134` WordPress settings read-only · CEREBRO — makeApiCall. Debe exponerse como lectura protegida plugin-first.
- `9551114` Extraer borradores REST — makeApiCall → feeder → datastore. Lectura/normalización debe pasar a plugin/runtime; no hay razón para mantener lógica pesada en Make.
- `9550846` Recuperar borradores locales — makeApiCall + aggregator. Lectura debe quedar plugin-first.
- `9695483` Inspección plantilla WordPress — makeApiCall. Debe quedar como ability/REST de lectura si sigue siendo necesaria.

### WRAP_WITH_CEREBRO · Make sí aporta bridge externo
- `9721021` Assets sociales Drive → WordPress CDN → Notion — Drive + createMediaItem + Notion. Mantener temporalmente porque Drive/Notion aportan valor de integración, pero la escritura WordPress debe migrar a Core Guard/Gateway. Make debe transportar, no decidir ni gobernar la mutación.

## Matriz de paridad Core Guard actual

| Capacidad | Make OLD | Core Guard actual | Estado |
|---|---|---|---|
| Health/readiness/smoke/status | varios diagnósticos | abilities nativas | GREEN_PLUGIN_FIRST |
| Snapshot de post/página | write/verify/rollback parcial | `capture-post-snapshot` | GREEN_PLUGIN_FIRST |
| Restore/rollback de post | escenarios manuales | `restore-post-snapshot` | GREEN_PLUGIN_FIRST |
| Purga cache URL | rutas Make históricas | `purge-cache-url` con gates | GREEN_PLUGIN_FIRST |
| Inspección WP/REST/settings | makeApiCall | REST/Abilities parciales | PARTIAL · ampliar lectura explícita |
| Duplicar página a borrador | `9542046` | no ability explícita | GAP |
| Actualizar contenido/SEO | `9681890`, `9556822`, otros | no ability explícita | GAP |
| Crear/subir media | `9721021`, `9721363` | no ability explícita | GAP |
| Bridge Drive/Notion | `9721021` | no es responsabilidad primaria del plugin | KEEP_BRIDGE |

## Gaps que Core Guard debe cubrir antes de retirar Make WordPress

1. Ability/ruta segura para duplicar página a borrador preservando metadatos/Elementor relevantes.
2. Ability/ruta para actualización de contenido/SEO con snapshot previo, lista blanca de campos y post-check.
3. Ability/ruta para subir media desde payload/URL controlada, con MIME/size/origin policy, checksum, metadata/alt text e idempotencia.
4. Lecturas explícitas para settings/template/drafts si siguen teniendo consumidores reales.
5. Contratos `company_id`, `engine_id`, `environment`, `version`, `correlation_id`, `idempotency_key` en la envoltura CEREBRO.
6. Evidencia OLD vs NEW para cada operación que hoy tenga equivalente Make.
7. Rollback probado antes de retirar cualquier escenario histórico.

## Política de mejora

Los huecos nuevos se implementan en rama de trabajo de `fenix-core-guard`, nunca directamente sobre WordPress PROD. Cada capability nueva debe incluir:
- capability/permisos mínimos;
- fail-closed `observer/apply` cuando escriba;
- snapshot previo en mutaciones de contenido;
- idempotency key y correlation id en la envoltura CEREBRO;
- validación de origen/tipo/tamaño donde aplique;
- post-check verificable;
- rollback;
- tests/quality gate;
- actualización de documentación y changelog.

## Regla de promoción

No tocar WordPress PROD para conseguir un check verde artificial.

`CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR`

Un escenario Make WordPress sólo puede retirarse cuando:
- mapa de dependencias = cerrado;
- Core Guard/Gateway cubre la misma capacidad o una mejor;
- tests y evidencia de paridad = verdes;
- snapshot/rollback = probado;
- no hay consumidor legacy;
- coste/riesgo del nuevo camino <= camino anterior.

## Siguiente loop

1. Construir las abilities faltantes una por una en rama de desarrollo de Core Guard, comenzando por lectura segura y después mutaciones con snapshot.
2. Añadir tests de contrato/quality gate antes de cada promoción.
3. Usar `9694471` únicamente como contrato OLD de referencia para write/verify/rollback, nunca como ejecución sobre PROD.
4. Mantener `9721021` como bridge temporal hasta que CEREBRO tenga ruta Drive/Notion equivalente o demuestre que Make sigue siendo el edge óptimo.
5. Actualizar Make audit y Engine Registry con el estado final por escenario.
