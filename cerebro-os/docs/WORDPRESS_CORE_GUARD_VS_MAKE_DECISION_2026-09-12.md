# CEREBRO OS · WordPress Core Guard vs Make · decisión canónica · 2026-09-12

## Estado observado

### EXISTENTE
- Repositorio independiente `carlosjmunoz78/fenix-core-guard`.
- La rama `production` contiene el plugin completo: core, 42 archivos `src/`, REST, WordPress Abilities/MCP, CEREBRO/Notion, jobs, snapshots/restore, cache orchestration, updater, rollback y quality gates.
- Namespace REST documentado: `fenix-guard/v1`.
- Capabilities documentadas: `fenix_guard_view`, `fenix_guard_manage`, `fenix_guard_repair`.
- Rutas documentadas incluyen health, policy, incidents, URLs, integrity, history, snapshots, restore, alerts, rules, audits, jobs, cache, changes y logs.
- Contrato CEREBRO ↔ Core Guard incluye correlación, idempotencia, firma HMAC, fail-closed y acciones controladas.

### POR AUDITAR / INCONSISTENCIA
- La rama `main` está muy por detrás y sólo contiene un bootstrap mínimo que referencia `src/` sin incluir el árbol completo.
- La rama `production` contiene la implementación real completa, pero su documentación sigue marcando el build RC9 como PRE-PROD y exige gates separados para PROD.
- No se debe inferir que el plugin está operativo en PROD sólo por existir la rama `production`; falta evidencia LIVE actual de instalación/version/health/readiness/observer/rollback.

## Decisión arquitectónica

**WordPress debe ser plugin-first.**

Orden de preferencia:
1. Fénix Core Guard / WordPress Abilities / MCP.
2. REST/API propia del plugin.
3. CEREBRO Gateway + motores WordPress/SEO.
4. Make sólo como bridge externo cuando aporte un conector SaaS que Core Guard no cubra o como transición temporal.

Make no debe actuar como CMS paralelo ni duplicar capacidades ya cubiertas por Core Guard.

## Clasificación de escenarios Make WordPress ya inspeccionados

### `9542046` · Duplicar página WordPress como borrador
- Flujo: getPost → createPost.
- Estado actual: inactive, 0 incomplete executions, conexión WordPress OK.
- Decisión: `REPLACE_AFTER_PARITY`.
- Razón: operación WordPress determinista que debe exponerse mediante Core Guard/Gateway con snapshot, idempotencia, policy y rollback.
- Acción: no activar; conservar como OLD hasta que exista ruta/ability equivalente y comparación OLD vs NEW.

### `9681890` · Corregir Córdoba · PROD autorizado
- Flujo: getPost → updatePost.
- Estado: inactive, 0 incomplete executions, conexión WordPress moderna OK.
- Decisión: `GREEN_QUARANTINED` + `REPLACE_AFTER_PARITY`.
- Razón: mutador PROD puntual/histórico; no debe convertirse en ruta permanente.

### `9721021` · Assets sociales · Drive → WordPress CDN
- Flujo: Google Drive → createMediaItem WordPress → Notion.
- Estado: inactive, 0 incomplete executions; Google Drive, WordPress y Notion connections OK.
- Decisión: `WRAP_WITH_CEREBRO`, no retirar todavía.
- Razón: Make sí aporta valor como bridge Drive/Notion, pero la escritura WordPress debe gobernarse por Core Guard/Gateway. La transformación y política deben salir de Make.

### PRE-PROD WordPress `9694499` / `9694504`
- Estado: inactive, fail-closed, secreto legacy retirado.
- Decisión: `GREEN_QUARANTINED` / `RETIRE_CANDIDATE` sólo después de demostrar paridad con Core Guard y no-consumidores.

## Gaps que Core Guard debe cubrir antes de retirar Make WordPress

1. Ability/ruta segura para duplicar página a borrador preservando metadatos/Elementor relevantes.
2. Ability/ruta para actualización de contenido/SEO con snapshot previo y post-check.
3. Ability/ruta para subir media desde payload/URL controlada, con MIME/size/origin policy y metadata/alt text.
4. Contratos `company_id`, `engine_id`, `environment`, `version`, `correlation_id`, `idempotency_key` en la envoltura CEREBRO.
5. Evidencia OLD vs NEW para cada operación que hoy tenga equivalente Make.
6. Rollback probado antes de retirar cualquier escenario histórico.

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

1. Auditar capabilities reales de `production` de Core Guard contra todos los escenarios Make WordPress.
2. Construir matriz `Make scenario → Core Guard ability/REST → engine consumer → estado migración`.
3. Identificar huecos del plugin y mejorarlo en rama de trabajo, no directamente en PROD.
4. Mantener Make sólo donde aporte bridge externo real.
5. Actualizar Make audit y Engine Registry con la decisión final por escenario.
