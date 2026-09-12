# CEREBRO OS · Market Intelligence + Make · gap real y arquitectura objetivo · 2026-09-12

## HECHO · evidencia Make viva

La búsqueda nominal de competencia en Make devuelve únicamente dos escenarios:
- `9557377` · CEREBRO SEO competitivo · URLs, embudos y canibalización · V2.
- `9557396` · CEREBRO SEO omnicanal · URLs, competencia y contenidos de apoyo · V3.

Ambos están `inactive`, `incompleteExecutions=0` y su blueprint real contiene únicamente `scenario-service` + tres lecturas `notion:makeApiCall` + retorno. No contienen HTTP, crawler, buscador, RSS, Google Maps, redes de competidores ni otra fuente externa. Por tanto **NO son colectores de competencia**. Son procesadores/lectores de conocimiento ya existente en Notion.

La búsqueda `mercado` no devuelve escenarios Make.

## RADAR 5/5 · clasificación cerrada

Los cinco escenarios RADAR existentes se han inspeccionado por blueprint y conexiones. Todos están inactivos, con `incompleteExecutions=0`, y todos corresponden a señales de activos/canales propios de Fénix, no a vigilancia de competidores:

- `9597297` · Facebook Página comentarios → Oportunidades · V1.1. `facebook-pages:ListPosts` → `ListComments` sobre conexión Fénix → Notion + Data Store con dedupe. `OWN_SOCIAL_SIGNAL`. Decisión: `WRAP_WITH_CEREBRO`; mantener inactivo hasta que exista consumidor contractual.
- `9595955` · Instagram comentarios → Oportunidades · V1. `GetUserMedia` → `listMediaComments` sobre conexión Fénix → Notion + Data Store con dedupe. `OWN_SOCIAL_SIGNAL`. Decisión: `WRAP_WITH_CEREBRO`; mantener inactivo hasta consumidor contractual.
- `9597307` · LinkedIn comentarios → Oportunidades · V2. `listOrganizationPosts2` → API comentarios → feeder → dedupe Notion → alta de oportunidad fail-closed. `OWN_SOCIAL_SIGNAL`. Decisión: `WRAP_WITH_CEREBRO` / `KEEP_INACTIVE_READY`.
- `9597372` · LinkedIn engagement → Inteligencia · V1. `listOrganizationPosts2` → estadísticas de shares → Data Store → Notion. `OWN_SOCIAL_SIGNAL`. Decisión: `WRAP_WITH_CEREBRO`; buen candidato a collector edge de bajo volumen si el coste por señal es bueno.
- `9597332` · YouTube comentarios canal → Oportunidades · V1.2. API YouTube oficial → Data Store → Notion con filtro de comentario nuevo. `OWN_SOCIAL_SIGNAL`. Decisión: `WRAP_WITH_CEREBRO` / `KEEP_INACTIVE_READY`.

Conclusión RADAR: **5/5 verificados; ninguno es collector competitivo**. Los conectores SaaS sí pueden seguir siendo útiles como edge, pero Notion/Data Store no deben ser la lógica ni el source of truth del nuevo runtime.

## CORRECCIÓN CANÓNICA

No se debe considerar que la capa de competencia ya existe sólo porque los nombres de algunos escenarios incluyan `competitivo`, `competencia` o `RADAR`.

Estado real:
- datos propios GSC/redes: EXISTENTE/PARCIAL con rutas Make útiles;
- procesamiento SEO/competencia basado en Notion: EXISTENTE pero `MIGRATE_TO_RUNTIME`/`WRAP_WITH_CEREBRO`;
- RADAR propios: EXISTENTE, 5/5 auditados, todos `OWN_SOCIAL_SIGNAL`;
- contrato `competitor_observation`: HECHO en runtime con validación de scope, hash, timezone, confidence, coste y dedupe;
- contrato `own_social_signal`: HECHO y CI VERDE con aislamiento `company_id/environment/version`, plataformas permitidas, tipos de señal, hash, timezone, confidence, coste y dedupe;
- colector web público de competencia + change detection + SQLite + market signal/action gate: EXISTENTE en LAB y cubierto por tests, sin promoción PROD;
- automatización multiempresa de alta de competidores y vigilancia periódica: PARCIAL / POR AUDITAR antes de producción autónoma.

## ARQUITECTURA OBJETIVO

Make se usa sólo donde aporte un conector barato/fiable. CEREBRO conserva la lógica y el histórico.

Pipeline:

`Company Registry → Business Discovery → Competitor Registry → collectors → observation contracts → dedupe/change detection → MKT-002 / RSH-001 / SCAN-001 / KW-001 / SOCAUD-001 / LOCALP-001 → scoring/comparison → opportunities/actions`

Contrato `competitor_observation` implementado:
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

Contrato `own_social_signal` implementado:
- `company_id`
- `engine_id`
- `environment`
- `version`
- `platform`
- `signal_type`
- `observed_at`
- `external_id`
- `source_account_id`
- `source_content_id`
- `value`
- `content_hash`
- `evidence_ref`
- `confidence`
- `cost_units`

Plataformas actualmente admitidas por contrato: `FACEBOOK`, `INSTAGRAM`, `LINKEDIN`, `YOUTUBE`. No se añade otra plataforma hasta existir collector/API y política verificadas.

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
- `9597297`, `9595955`, `9597307`, `9597372`, `9597332` → `WRAP_WITH_CEREBRO` y permanecer inactivos hasta adaptador Make→`own_social_signal` + consumidor + coste medido; categoría canónica `OWN_SOCIAL_SIGNAL`.
- GSC PROD → `KEEP_ACTIVE` mientras siga aportando datos propios con coste/fiabilidad aceptables.

## TEST/TEMP · evidencia adicional

La partición nominal `TEMP` de TEST ha sido revisada: nueve escenarios devueltos, todos `inactive` y `incompleteExecutions=0`. Incluye auditorías/lecturas temporales, export GSC, WordPress ya absorbible por Core Guard, bridge Drive→WordPress→Notion y verificación FB puntual. No se reactiva ninguno sólo por estar inventariado.

La partición `DEPRECATED` devuelve 25 escenarios legacy en el límite de Make, todos `inactive` y `incompleteExecutions=0`, dominados por gates/dry-runs/staging/publicadores Facebook/Instagram marcados explícitamente `NO USAR`; se mantienen como `GREEN_QUARANTINED` hasta completar mapa de dependencias, sin convertirlos de nuevo en runtime.

## SIGUIENTE LOOP TÉCNICO

1. Crear adaptador determinista Make/RADAR → `own_social_signal` sin mover decisión a Make.
2. Mantener los cinco RADAR inactivos hasta que adaptador + consumidor + coste estén verdes.
3. Completar inventario único 120/120 TEST y 62/62 CORE con target state por escenario.
4. Probar OLD vs NEW de `9557377/9557396` y migrar su lógica a runtime compartido.
5. Completar onboarding multiempresa de competidores con fuentes permitidas y budgets por collector.
6. Medir coste real por señal antes de asignar créditos Make estables.

## PROMOCIÓN

Ningún collector de competencia ni RADAR pasa a PROD autónomo sin fuente permitida, contrato, dedupe, rate limit, evidencia, observabilidad, coste medido, rollback/disable y política de datos.
