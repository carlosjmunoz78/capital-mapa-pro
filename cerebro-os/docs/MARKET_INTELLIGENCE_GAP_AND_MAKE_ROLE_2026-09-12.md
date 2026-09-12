# CEREBRO OS · Market Intelligence + Make · gap real y arquitectura objetivo · 2026-09-12

## HECHO · evidencia Make viva

La búsqueda nominal de competencia en Make devuelve únicamente dos escenarios:
- `9557377` · CEREBRO SEO competitivo · URLs, embudos y canibalización · V2.
- `9557396` · CEREBRO SEO omnicanal · URLs, competencia y contenidos de apoyo · V3.

Ambos están `inactive`, `incompleteExecutions=0` y su blueprint real contiene únicamente `scenario-service` + tres lecturas `notion:makeApiCall` + retorno. No contienen HTTP, crawler, buscador, RSS, Google Maps, redes de competidores ni otra fuente externa. Por tanto **NO son colectores de competencia**. Son procesadores/lectores de conocimiento ya existente en Notion.

La búsqueda `mercado` no devuelve escenarios Make.

Los cinco escenarios `RADAR` existentes tampoco constituyen por sí mismos inteligencia competitiva:
- `9597297` Facebook Página comentarios → Oportunidades.
- `9595955` Instagram comentarios → Oportunidades.
- `9597307` LinkedIn comentarios → Oportunidades.
- `9597372` LinkedIn engagement → Inteligencia.
- `9597332` YouTube comentarios canal → Oportunidades.

El blueprint verificado de `9597297` usa `facebook-pages:ListPosts` + `ListComments` sobre la conexión de Fénix y genera oportunidades con dedupe/idempotencia. Es captura de **datos propios / audiencia propia**, no observación de competidores.

## CORRECCIÓN CANÓNICA

No se debe considerar que la capa de competencia ya existe sólo porque los nombres de algunos escenarios incluyan `competitivo`, `competencia` o `RADAR`.

Estado real:
- datos propios GSC/redes: EXISTENTE/PARCIAL con rutas Make útiles;
- procesamiento SEO/competencia basado en Notion: EXISTENTE pero `MIGRATE_TO_RUNTIME`/`WRAP_WITH_CEREBRO`;
- colector sistemático de competencia/mercado: **GAP REAL**;
- scoring/normalización/almacenamiento contractual de observaciones competitivas: DEFINIDO por arquitectura CEREBRO, no probado como runtime completo;
- automatización multiempresa de alta de competidores y vigilancia periódica: PLANIFICADO/POR AUDITAR.

## ARQUITECTURA OBJETIVO

Make se usa sólo donde aporte un conector barato/fiable. CEREBRO conserva la lógica y el histórico.

Pipeline:

`Company Registry → Business Discovery → Competitor Registry → collectors → observation contracts → dedupe/change detection → MKT-002 / RSH-001 / SCAN-001 / KW-001 / SOCAUD-001 / LOCALP-001 → scoring/comparison → opportunities/actions`

Contrato mínimo de observación:
- `company_id`
- `competitor_id`
- `engine_id`
- `environment`
- `version`
- `source`
- `source_type`
- `observed_at`
- `url_or_external_id`
- `metric_or_fact`
- `value`
- `content_hash`
- `evidence_ref`
- `confidence`
- `cost_units`

## FUENTES Y RUTA ÓPTIMA

### Web/SEO público
Preferencia: runtime Python/TypeScript + HTTP/crawler respetuoso + sitemap/robots + parsers deterministas. Make sólo para APIs/RSS/webhooks donde simplifique mucho la integración.

Recoger: nuevas URLs, titles/H1, schema, canonical, sitemap, cambios de contenido, landings, categorías, ofertas visibles, CTAs, estructura de embudo y frecuencia de cambios.

### Search / keywords
GSC es únicamente dato propio. Para competencia: fuentes públicas, SERP/búsqueda permitida, páginas indexadas/landing visibles y herramientas ya contratadas/conectadas cuando aporten valor sin nueva suscripción.

### Social
Make puede ser edge cuando el conector/API permita leer señales públicas de forma válida. No asumir que una conexión de cuenta propia permite observar cuentas competidoras. Cada plataforma se valida por API/permisos/términos antes de activar.

### Local SEO / presencia
Recoger perfiles, NAP, categorías, reseñas/ratings públicos, cambios de ficha, presencia por localidad y directorios mediante fuentes permitidas. Procesamiento y comparación fuera de Make.

### Contenido / noticias / feeds
RSS/APIs/web público → collector ligero → contrato de observación → CEREBRO. Preferir delta/hash sobre crawling completo.

## USO DE LOS 10.000 CRÉDITOS MAKE

No reservar 2.500 créditos de competencia por defecto hasta tener colectores reales medidos. Ese presupuesto es techo dinámico.

Fase inicial de aprendizaje:
- máximo 500–1.000 créditos/mes para prototipos/collectors externos de alta señal;
- medir `credits_per_detected_change`, `credits_per_useful_signal` y `credits_per_actionable_insight`;
- mover a runtime cualquier fuente cuyo coste por señal útil sea peor que API/código directo;
- subir presupuesto únicamente cuando exista evidencia de ROI y estabilidad.

Los créditos no se queman para completar cuota. Se asignan al collector que aporte más información útil por crédito.

## DECISIÓN SOBRE ESCENARIOS EXISTENTES

- `9557377` → `MIGRATE_TO_RUNTIME` como lógica de composición/análisis; conservar como OLD hasta paridad.
- `9557396` → `MIGRATE_TO_RUNTIME` como lógica de composición/análisis; conservar como OLD hasta paridad.
- `9597297`, `9595955`, `9597307`, `9597372`, `9597332` → `WRAP_WITH_CEREBRO`/`KEEP_INACTIVE_READY` según fuente y coste; clasificarlos como `OWN_SOCIAL_SIGNAL`, no competencia.
- GSC PROD → `KEEP_ACTIVE` mientras siga aportando datos propios con coste/fiabilidad aceptables.

## SIGUIENTE LOOP TÉCNICO

1. No activar los escenarios `competitivo` pensando que recolectan competencia: no lo hacen.
2. Construir el contrato canónico `competitor_observation` y su validación multiempresa.
3. Construir primero collector web/SEO público determinista y barato fuera de Make.
4. Construir después adaptadores de fuentes sociales/locales sólo donde las APIs/permisos lo permitan.
5. Envolver los RADAR propios como `own_social_signal` y dirigirlos a motores CEREBRO.
6. Probar OLD vs NEW de `9557377/9557396` y migrar su lógica a runtime compartido.
7. Medir coste real por señal antes de asignar créditos Make estables.

## PROMOCIÓN

Ningún collector de competencia pasa a PROD autónomo sin fuente permitida, contrato, dedupe, rate limit, evidencia, observabilidad, coste medido, rollback/disable y política de datos.
