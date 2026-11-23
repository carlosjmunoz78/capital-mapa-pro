# CE-05 · CP72 · Coherencia de estados en cola de propuestas

## Defecto anterior

`ProposalQueue.upsert` conservaba la columna `status` en SQLite, pero reemplazaba el `payload_json` con el estado de la nueva ingesta. Esto permitía un registro con `status=WAITING_TEST` y `payload_json.status=OPEN`, ocultando el estado efectivo al consultar `list_open`. En propuestas `CLOSED`, una importación repetida cambiaba metadatos sin reabrir formalmente el expediente. La validación también aceptaba `cost_limit_eur=NaN/Infinity`.

## Comportamiento nuevo

- El `upsert` hace `BEGIN IMMEDIATE` y conserva en el JSON el estado confirmado de SQLite.
- En estados `CLOSED`, `BLOCKED` y `HUMAN_REQUIRED`, la ingesta no altera filas existentes. Cambios expresos de estado siguen siendo un flujo separado (`set_status`).
- No permite incrementar `cost_limit_eur` para una clave de evidencia existente; sí preserva las actualizaciones legítimas de identificador y prioridad mientras la fila es abierta.
- Rechaza valores de coste no finitos sin alterar otras propuestas.
- `list_open()` usa el estado SQLite como autoridad para leer filas de formatos históricos potencialmente inconsistentes.
- Sin cambios del esquema SQLite, sin nuevas tablas, sin migración, sin publicación y sin despliegue remoto.

## Evidencias y rollback

- OLD: 12 pruebas ejecutadas, 6 fallos reproducibles.
- NEW: 12/12 pruebas correctas, incluidos 4 tests preexistentes de importación, orden, deduplicación y política.
- `test_old.log` y `test_new.log` incluidos.
- Se verificó `git revert` en repositorio sintético aislado, restaurando el mismo Git tree de la base.
- Ramas LAB independientes; coste adicional de infraestructura 0 €.
- Límites: no es evidencia de firma del emisor, seguridad de DBA ni autorización de promoción. El flujo explícito `set_status` conserva sus contratos actuales y requiere su propio gate antes de publicación.