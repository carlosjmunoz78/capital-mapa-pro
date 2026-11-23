# CE-05 · CP73 · Transiciones gobernadas de propuestas

## Contrato conservado

No se altera el esquema de `proposal_queue`, el identificador fingerprint, ni la API pública `set_status(fingerprint, status)`. Es un guard de seguridad LAB. `set_status` sigue siendo una acción explícita y solo se usa tras los gates correspondientes.

## OLD → NEW

OLD permite que cualquier `set_status` reabra un registro `CLOSED`, `BLOCKED` o `HUMAN_REQUIRED`, incluso si el `upsert` CP72 impide reabrirlo por replay. También permite `WAITING_TEST -> OPEN`. NEW bloquea esas transiciones mediante comparación atómica bajo `BEGIN IMMEDIATE`, conserva reintentos idénticos y deja proseguir `OPEN -> WAITING_TEST -> CLOSED/BLOCKED/HUMAN_REQUIRED` y `OPEN -> CLOSED` cuando el flujo existente así lo decide. No se introduce aprobación humana simulada ni automación comercial.

Los registros históricos que ya tienen `status` SQLite y `payload_json.status` divergentes se alinean únicamente cuando reciben una transición explícita autorizada; no se realiza una migración o barrido global.

## Pruebas

- 21 casos, OLD 5 fallos reproducidos y NEW 21/21 correctos. Incluye 4 tests del importador preexistente, 8 de CP72 y 9 nuevos de CP73.
- Dos conexiones SQLite comprueban que la segunda no reabre una decisión terminal.
- Rollback sintético de Git con restauración exacta del árbol original.

## Limitaciones

Este guard evita cambios accidentales del software, no autentica por sí mismo al operador que invoca `set_status` ni sustituye controles IAM, el tribunal o un journal externo firmado. Gateway OFF, envíos Brevo suspendidos, sin cambios en producción. Coste adicional 0 €.