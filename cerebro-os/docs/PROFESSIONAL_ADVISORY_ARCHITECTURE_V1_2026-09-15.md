# CEREBRO PROFESSIONAL ADVISORY · ARCHITECTURE V1

## Decisión estructural

PROFESSIONAL_ADVISORY es una capability/orchestration layer, no un engine_id nuevo por defecto.

Fiscal, Contable, Laboral, Mercantil, Financiera, Inmobiliaria, Hipotecaria, Subvenciones/Ayudas, Protección de Datos/Compliance, Empresarial/Estratégica, Patrimonial y Jurídica General son especialidades coordinables dentro de un expediente único.

## Regla de composición

Un dominio de asesoría puede reutilizar uno o varios engine_ids canónicos existentes. La ausencia de un engine_id dedicado no convierte el dominio en inexistente ni obliga a inventar un ID. Solo se crea un engine nuevo si el análisis de responsabilidad, estado y contrato demuestra que la capacidad no puede componerse de forma segura con piezas existentes.

## Expediente único

Entrada mínima:
- company_id
- case_id
- environment
- version
- requested_service
- territory
- facts
- evidence

Salida por especialidad:
- status
- summary
- source_refs
- risks
- deadlines
- next_actions
- human_exception, cuando proceda

## Routing

El router puede activar múltiples dominios para el mismo expediente. Ejemplo de patrón válido: compra inmobiliaria por sociedad -> Inmobiliaria + Fiscal + Contable + Mercantil + Financiera + Patrimonial.

## Fuentes

Los repositorios PRO originales se conservan como fuentes. Los artefactos derivados (índices, contratos, reglas, casos, tests y embeddings si algún día se usan) deben mantener source_id/source_version/provenance y nunca sustituir silenciosamente el original.

## TAX-001

TAX-001 conserva todo su trabajo anterior, pero queda conceptualmente situado debajo de la especialidad FISCAL. No representa PROFESSIONAL_ADVISORY completo.

## Estado de fuentes recibido en este corte

Disponibles: Fiscal, Contable, Laboral FINAL v1.0, Mercantil, Financiera, Inmobiliaria, Hipotecaria, Subvenciones/Ayudas, Protección de Datos/Compliance, Empresarial/Estratégica y Patrimonial.

Laboral v0.1 se conserva como histórico y queda supersedido para nueva construcción por Laboral v1.0 FINAL.

Jurídica General: MISSING_ARTIFACT en este corte. LEG-001 puede aportar lógica transversal, pero no debe usarse para inventar un repositorio jurídico general que no haya sido entregado.

## Gates

- No App/CRM/PROD mutation.
- No new engine IDs without evidence.
- No capability/autonomy promotion from documentation alone.
- HUMAN_REQUIRED limited to canonical taxonomy.
- 0 EUR additional cost default.
- Cross-domain decisions must preserve per-domain evidence and responsibility.
