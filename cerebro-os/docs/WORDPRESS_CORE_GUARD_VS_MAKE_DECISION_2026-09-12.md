# CEREBRO OS · WordPress Core Guard vs Make · decisión canónica · 2026-09-12

## Estado observado

### EXISTENTE
- Repositorio independiente `carlosjmunoz78/fenix-core-guard`.
- La rama `production` contiene el plugin completo: core, 42 archivos `src/`, REST, WordPress Abilities/MCP, CEREBRO/Notion, jobs, snapshots/restore, cache orchestration, updater, rollback y quality gates.
- Namespace REST documentado: `fenix-guard/v1`.
- Capabilities documentadas: `fenix_guard_view`, `fenix_guard_manage`, `fenix_guard_repair`.
- Rutas documentadas incluyen health, policy, incidents, URLs, integrity, history, snapshots, restore, alerts, rules, audits, jobs, cache, changes y logs.
- Contrato CEREBRO ↔ Core Guard incluye correlación, idempotencia, firma HMAC, fail-closed y acciones controladas.
- WordPress Abilities base verificadas: `health`, `preprod-readiness`, `smoke-test`, `cerebro-status`, `capture-post-snapshot`, `purge-cache-url`, `restore-post-snapshot`.

### HECHO · rama development endurecida
La rama `development` ya incorpora y tiene quality gate verde para:
- `fenix-core-guard/post-inspect` — lectura segura de metadatos de post/página.
- `fenix-core-guard/duplicate-page-draft` — duplicación controlada a borrador bajo gate `apply` + confirmación.
- `fenix-core-guard/update-page-draft` — update de borrador con snapshot previo, post-check y rollback automático si falla.
- `fenix-core-guard/upload-jpeg-base64` — media JPEG controlada con límite 5 MiB, validación MIME real, checksum y eliminación si falla el post-check.
- `fenix-core-guard/list-page-drafts` — lectura segura y acotada de borradores de página, sin exponer contenido completo.

El workflow de desarrollo `Core Guard Quality Gate` para el commit `85ab0d3ef8e9bfa2ccb8d0ca4d741bb3eb12ca21` finalizó `success`, incluyendo gates de lectura segura, draft update y media upload.

### POR AUDITAR / INCONSISTENCIA
- La rama `main` está muy por detrás y sólo contiene un bootstrap mínimo.
- La rama `production` contiene implementación completa pero sigue documentada como RC9 PRE-PROD; no confundir nombre de rama con despliegue live.
- Falta evidencia LIVE actual de instalación/version/health/readiness/observer/rollback en WordPress real.
- Las nuevas abilities están verdes en código/CI de `development`, pero aún no se consideran operativas LIVE ni autorizadas en PROD.
- La lectura genérica de settings WordPress sigue sin justificarse como capability estable hasta identificar consumidor y allowlist exacta.

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
- `9542046` Duplicar página WordPress como borrador — paridad de código disponible en `development` mediante `duplicate-page-draft`; pendiente OLD vs NEW + LIVE controlado.
- `9694471` CEREBRO SEO write-verify-rollback — conservar como contrato OLD de prueba; el camino nuevo usa snapshot/post-check/rollback plugin-first.
- `9540674` Corregir footer codificado — mutación específica legacy; no crear ability genérica peligrosa. Resolver sólo mediante operación allowlisted si sigue existiendo consumidor.
- `9556822` Reconstruir landing SEO en borrador — paridad de código disponible en `development` mediante `update-page-draft`; pendiente OLD vs NEW + LIVE controlado.
- `9721363` Upload JPEG base64 → WordPress — paridad de código disponible mediante `upload-jpeg-base64`; pendiente OLD vs NEW + LIVE controlado.

### MIGRATE_TO_PLUGIN_READ_API
- `9557305` Inspección rutas REST WordPress — sustituible por Core Guard REST/MCP; conservar sólo hasta cerrar consumidores.
- `9773134` WordPress settings read-only · CEREBRO — mantener inactivo; no ampliar plugin hasta saber exactamente qué settings necesita el consumidor.
- `9551114` Extraer borradores REST — capacidad de lectura cubierta en código por `list-page-drafts`; pendiente paridad de salida/consumidor.
- `9550846` Recuperar borradores locales — capacidad base cubierta por `list-page-drafts`; pendiente confirmar semántica legacy exacta.
- `9695483` Inspección plantilla WordPress — cubierta por `post-inspect` para un ID concreto.

### WRAP_WITH_CEREBRO · Make sí aporta bridge externo
- `9721021` Assets sociales Drive → WordPress CDN → Notion — Drive + createMediaItem + Notion. Mantener temporalmente porque Drive/Notion aportan valor de integración, pero la escritura WordPress debe migrar a Core Guard/Gateway. Make transporta; CEREBRO gobierna.

## Matriz de paridad

| Capacidad | Make OLD | Core Guard development | Estado |
|---|---|---|---|
| Health/readiness/smoke/status | diagnósticos varios | abilities nativas | GREEN_CODE_CI |
| Snapshot | write/verify/rollback parcial | `capture-post-snapshot` | GREEN_CODE_CI |
| Restore/rollback | escenarios manuales | `restore-post-snapshot` | GREEN_CODE_CI |
| Purga cache URL | rutas legacy | `purge-cache-url` | GREEN_CODE_CI |
| Inspección página/template | makeApiCall | `post-inspect` | GREEN_CODE_CI |
| Listar borradores página | REST/feeder/Data Store | `list-page-drafts` | GREEN_CODE_CI |
| Duplicar página a borrador | `9542046` | `duplicate-page-draft` | GREEN_CODE_CI · PARITY_PENDING |
| Actualizar borrador SEO/contenido | `9556822` | `update-page-draft` | GREEN_CODE_CI · PARITY_PENDING |
| Subir JPEG base64 | `9721363` | `upload-jpeg-base64` | GREEN_CODE_CI · PARITY_PENDING |
| Bridge Drive/Notion | `9721021` | fuera de responsabilidad primaria del plugin | KEEP_BRIDGE |
| Settings genéricos | `9773134` | no expuesto deliberadamente | NEED_CONSUMER_CONTRACT |

## Gaps restantes antes de retirar Make WordPress

1. Pruebas OLD vs NEW controladas para duplicación, update de borrador y media; nunca sobre contenido PROD no reversible.
2. Contratos `company_id`, `engine_id`, `environment`, `version`, `correlation_id`, `idempotency_key` en Gateway/CEREBRO alrededor de las abilities.
3. Identificar consumidores reales de settings/rutas REST legacy antes de crear allowlists adicionales.
4. Evidencia LIVE de instalación/version/health/readiness/observer y rollback del plugin.
5. Confirmar no-consumidores y mapa de dependencias antes de retirar cada escenario Make.
6. Mantener `9721021` como bridge externo mientras siga siendo más eficiente que duplicar Drive/Notion en código.

## Política de mejora

Los huecos se implementan en `development`, nunca directamente en WordPress PROD. Cada capability nueva exige permisos mínimos, fail-closed, validación, post-check, rollback cuando aplique, tests y actualización documental.

## Regla de promoción

No tocar WordPress PROD para conseguir un check verde artificial.

`CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR`

Un escenario Make WordPress sólo puede retirarse cuando mapa de dependencias, paridad, tests, rollback y no-consumidores estén verdes.

## Siguiente loop

1. Cerrar contratos Gateway multiempresa/idempotencia alrededor de las nuevas abilities.
2. Diseñar fixtures OLD vs NEW para `9542046`, `9556822`, `9721363` sin tocar contenido real.
3. Auditar consumidor exacto de `9773134` antes de exponer settings.
4. Mantener `9721021` como bridge temporal y medir coste/valor.
5. Promover abilities sólo tras staging/live controlado y rollback probado.
