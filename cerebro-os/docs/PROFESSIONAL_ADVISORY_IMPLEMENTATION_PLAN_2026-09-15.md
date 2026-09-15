# CEREBRO PROFESSIONAL ADVISORY · PLAN DE IMPLEMENTACIÓN V1

Fecha: 2026-09-15
Entorno: LAB
Principio: preservar los repositorios originales; Fiscal es una especialidad, no la asesoría completa.

## Secuencia de cierre

1. Inventariar repositorios originales y elegir versión canónica por dominio.
2. Fijar arquitectura superior PROFESSIONAL_ADVISORY como orquestador de capacidades.
3. Crear catálogo canónico de dominios y relaciones con engine_ids existentes, sin inventar IDs.
4. Definir contrato común de expediente Advisory: company_id, case_id, environment, version, territory, facts, evidence, sources, deadlines, risks, outputs, referrals.
5. Definir router interdisciplinar determinista: un expediente puede activar varias especialidades.
6. Definir modelo de fuente/repositorio: source_document preservado + hash + versión + estado + mantenimiento.
7. Reposicionar TAX-001 como capability fiscal bajo Advisory, sin borrar ni degradar su trabajo previo.
8. Añadir tests de invariantes: 12 dominios, Fiscal no-root, no IDs inventados, cross-domain permitido, HUMAN_REQUIRED canónico.
9. Ejecutar CI y fusionar solo si GREEN.
10. Incorporar conocimiento completo dominio por dominio desde documentos físicos, conservando estructura original y generando índices/artefactos derivados.
11. Cerrar Jurídica General cuando exista su repositorio maestro físico; mientras tanto MISSING_ARTIFACT, no inventar contenido.
12. Tribunal final Advisory Knowledge/Capability separado de PROD y autonomía.

## Regla de promoción

Un punto pasa a VERDE solo con artefacto verificable + tests cuando aplique. LAB_GREEN no equivale a PROD ni a autoridad profesional regulada.
