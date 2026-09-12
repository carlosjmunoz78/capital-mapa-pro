# CEREBRO OS · Rol óptimo de Make + estrategia de 10.000 créditos/mes · 2026-09-12

## Decisión
Make se conserva como **edge de integración, captura y ejecución** dentro de CEREBRO OS, no como cerebro, source of truth ni runtime universal.

Regla canónica:

`fuente externa / SaaS -> Make cuando el conector aporta valor -> evento/contrato CEREBRO -> procesamiento determinista compartido -> almacenamiento canónico -> motores de inteligencia/decisión -> acción por Gateway/políticas`

Cuando Make no aporta una ventaja clara frente a código/cron/API directa, se prioriza código compartido, GitHub Actions, workers Python/TypeScript o conectores nativos ya existentes.

## Excepción explícita WordPress
WordPress es **plugin-first** mediante Fénix Core Guard / WordPress Abilities / MCP / REST propia. Make no se considera conector WordPress preferente por defecto. Sólo se conserva como bridge temporal o para integrar un SaaS externo que Core Guard/Gateway no cubra todavía. Cualquier escritura WordPress en Make queda sujeta a `REPLACE_AFTER_PARITY` salvo justificación documentada.

## Evidencia del proyecto
Los documentos canónicos ya establecen que:
- AUTBOOT-001 debe usar plantillas event-driven y "código/GitHub/cron antes que Make si no aporta valor".
- INT-001 debe mantener inventario vivo de readers/writers/webhooks/tokens/owners/health de integraciones, incluido Make.
- MKT-002 debe combinar fuentes públicas, GSC/GA4 y Research para demanda, competencia, precios, búsquedas, zonas y señales.
- SCAN-001, KW-001, WAUD-001, SOCAUD-001, LOCALP-001, SEOBOOT-001, SOCBOOT-001 y MKTBOOT-001 forman parte del onboarding multiempresa.
- Technology Scout debe evaluar continuamente herramientas existentes antes de introducir otras nuevas.

## Evidencia Make viva
Escenarios actuales relevantes localizados:
- Competencia/SEO: `9557377` Cerebro SEO competitivo · URLs, embudos y canibalización; `9557396` SEO omnicanal · URLs, competencia y contenidos de apoyo.
- RADAR: `9597297` Facebook comentarios; `9595955` Instagram comentarios; `9597307` LinkedIn comentarios; `9597372` LinkedIn engagement; `9597332` YouTube comentarios.
- Datos propios/SEO: `9597710` GSC 30d -> Inventario Notion activo en PROD; otros escenarios GSC/SEO históricos o TEST conservados.
- WordPress: 17 escenarios nominales auditados; todos inactivos y sin ejecuciones incompletas. Los mutadores quedan cuarentenados o `REPLACE_AFTER_PARITY`; sólo el bridge Drive → WordPress → Notion conserva valor claro de integración externa mientras se migra la mutación WordPress a Core Guard/Gateway.

Los RADAR y competitivos están hoy inactivos. Se conservan como activos funcionales potenciales y no se eliminan sólo por estar apagados.

## Qué debe hacer Make en la arquitectura objetivo
### USAR MAKE
1. Conectores SaaS que ya funcionan y reducen código de integración: Google Search Console, GA4, Meta/Instagram/Facebook, LinkedIn, YouTube, Notion y equivalentes cuando el conector tenga mejor coste/fiabilidad que mantener código propio.
2. Webhooks y eventos de entrada de baja latencia.
3. Polling ligero de APIs cuando no exista webhook.
4. Normalización mínima, dedupe/idempotencia de borde y entrega del evento al Gateway/Runtime CEREBRO.
5. Reconciliaciones, health checks y avisos donde una ejecución de Make evita mantener infraestructura adicional.
6. Captura de datos propios y señales públicas/permitidas de competencia cuando la fuente y términos lo permitan.
7. Bridges externos puntuales hacia WordPress sólo cuando integren un SaaS externo y mientras Core Guard/Gateway no ofrezca paridad.

### NO USAR MAKE COMO PRIMERA OPCIÓN
1. Operaciones WordPress que Fénix Core Guard/Abilities/REST pueda cubrir o deba cubrir: lectura técnica, snapshots, restore, cache, actualización de contenido, media o mantenimiento.
2. Transformaciones masivas, loops grandes o backfills históricos.
3. Scraping intensivo o crawling de miles de URLs.
4. Almacenamiento histórico pesado.
5. Entrenamiento, embeddings, OCR pesado, simulación o jobs largos.
6. Lógica de decisión, scoring estratégico, políticas o tribunal.
7. IA de pago dentro de Make cuando Python/TypeScript/local/model router pueda resolverlo con menor coste.
8. Duplicar source of truth de Supabase/CRM/Notion/GSC/GA4.

## Pipeline objetivo de inteligencia
### Datos propios
- GSC/GA4 -> captor Make cuando sea eficiente -> contrato `own_signal` -> MKT-002/SEO-001/OBS-001.
- Redes propias -> Make/API -> `social_signal` -> SOCAUD-001/SOCBOOT-001/OPP-001.
- CRM/App -> eventos directos/Gateway; Make sólo si conecta un SaaS externo.
- WordPress -> Core Guard/Abilities/MCP/REST → Gateway/CEREBRO. Make sólo como bridge externo temporal, nunca como CMS paralelo.

### Competencia y mercado
- Fuentes públicas/RSS/APIs/búsqueda -> SCAN-001/MKT-002/RSH-001.
- GSC/GA4 sólo para datos propios; no tratar sus métricas como datos de competidores.
- Competidores: web/SEO/huella/redes/presencia local/feeds públicos -> contratos de observación separados por `company_id`, `competitor_id`, `source`, `observed_at`, `environment`, `version`.
- Make se usa como transportador/conector donde el API/RSS/conector sea ventajoso; crawling y comparación pesada pasan al runtime compartido.

## Presupuesto operativo de 10.000 créditos/mes
Los 10.000 créditos son un **presupuesto máximo útil**, no un objetivo de quemado. El objetivo es maximizar señal útil por crédito, no consumir 100% artificialmente.

Asignación inicial recomendada, revisable por FINOPS-001/OPT-001:
- 30% (3.000): datos propios críticos — GSC/GA4/redes/CRM-edge.
- 25% (2.500): competencia + market intelligence de alta señal.
- 15% (1.500): reconciliación, health, watchdog y detección de fallos.
- 10% (1.000): RADAR social/oportunidades.
- 10% (1.000): automatizaciones operativas de negocio que eviten trabajo humano.
- 10% (1.000): reserva dinámica para picos, onboarding de empresas y backfills pequeños.

Los escenarios WordPress redundantes no reciben presupuesto operativo una vez exista paridad plugin-first; los créditos liberados vuelven a competencia, datos propios y reserva.

Gates mensuales:
- 0-70%: normal.
- 70-85%: reducir polling de baja señal, agrupar lecturas, preferir webhooks.
- 85-95%: sólo rutas prioritarias y eventos con ROI medible.
- >95%: bloquear cargas no críticas y derivar a runtime/código; no comprar créditos extra automáticamente sin MONEY_LIMIT/ROI.

## Optimización por crédito
- Preferir webhook/evento a polling.
- Polling adaptativo: más frecuencia sólo cuando hay cambios.
- Leer delta desde `last_cursor/last_seen`, no ventanas completas.
- Filtrar antes de ramificar módulos.
- Agrupar payloads y hacer transformación pesada fuera de Make.
- Dedupe antes de writers.
- Separar collectors de processors: Make captura; CEREBRO procesa.
- Medir `credits_per_useful_signal`, `credits_per_lead`, `credits_per_detected_change`, `credits_per_successful_action`.

## Estados para los escenarios existentes
Cada escenario debe terminar en uno de estos estados canónicos:
- `KEEP_ACTIVE`: aporta valor, contrato claro, coste aceptable, evidencia runtime.
- `KEEP_INACTIVE_READY`: útil pero no necesita estar programado ahora.
- `GREEN_QUARANTINED`: histórico/TEST/mutador riesgoso que se conserva sin activar.
- `WRAP_WITH_CEREBRO`: buen conector, pero la lógica debe pasar a Gateway/engine.
- `MIGRATE_TO_RUNTIME`: Make aporta poco y consume créditos/complejidad innecesaria.
- `REPLACE_AFTER_PARITY`: sólo retirar tras OLD vs NEW + rollback probado.
- `RETIRE_CANDIDATE`: sin consumidores ni valor, pendiente de mapa de dependencias y evidencia antes de borrar.

## Criterio de decisión por escenario
Score 0-5 para: valor de negocio, unicidad del conector, coste en créditos, riesgo, mantenibilidad, frecuencia, volumen, lock-in, latencia, observabilidad y facilidad de migración.

Decisión:
- conector alto + volumen bajo/medio -> Make.
- conector bajo + volumen alto -> runtime/código.
- WordPress interno -> Core Guard/Gateway primero; Make sólo bridge externo justificado.
- lógica compleja -> engine CEREBRO, aunque Make siga como borde.
- acción sensible -> Gateway + Policy Engine; Make nunca decide por sí solo.

## Siguiente ejecución técnica
1. Completar inventario 120/120 TEST y 62/62 CORE.
2. Añadir a cada escenario: función, source, destination, reader/writer, owner, criticidad, créditos, frecuencia, consumer engine y estado objetivo.
3. Mapear los escenarios de competencia/RADAR contra MKT-002, SCAN-001, KW-001, WAUD-001, SOCAUD-001, LOCALP-001, OPP-001 y SEO-001.
4. Implementar en Core Guard las capacidades WordPress faltantes antes de retirar Make: lectura segura, duplicación de borrador, update contenido/SEO y media controlada.
5. Calcular el presupuesto mensual previsto y evitar rutas que excedan 10k.
6. Elegir uno a uno KEEP / WRAP / MIGRATE / QUARANTINE / RETIRE_CANDIDATE.
7. No activar colectores de competencia hasta verificar fuente, permisos/términos, contrato de datos, coste y destino.
8. Promover sólo con evidencia runtime, observabilidad y rollback.

## Resultado esperado
Make queda aprovechado donde tiene ventaja real: conectores, webhooks, SaaS y captura de señales. CEREBRO queda como sistema de decisión, almacenamiento contractual, inteligencia y gobierno. WordPress queda gobernado por Core Guard/Gateway. Esto conserva la inversión existente, reduce lock-in, usa los 10.000 créditos donde más valor generan y mantiene la arquitectura multiempresa preparada para crecer sin convertir Make en un cuello de botella.
