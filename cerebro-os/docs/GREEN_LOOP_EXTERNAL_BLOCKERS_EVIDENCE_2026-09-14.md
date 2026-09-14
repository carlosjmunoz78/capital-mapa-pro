# CEREBRO OS · GREEN LOOP · BLOQUEOS EXTERNOS CON EVIDENCIA · 2026-09-14

## Objetivo

Separar lo que CEREBRO puede cerrar de forma autónoma y segura de lo que exige una excepción humana canónica o una evidencia externa que hoy no existe. Este documento no concede permisos de PROD ni autoriza gastos.

## SECURITY · authenticated HTTP E2E

Estado: `PARTIAL / HUMAN_REQUIRED: HIGH_RISK`.

Evidencia live:
- `CARLOS-ADMIN` está activo y enlazado a Auth.
- `BELEN-DIR` está activo y enlazado a Auth.
- `ANA-SYSTEM` está activo pero no enlazado a Auth.
- No se ha probado una identidad dedicada de test autenticada en PROD.

Decisión fail-closed:
- No reutilizar automáticamente identidades humanas reales para un E2E destructivo o de escritura.
- No insertar usuarios directamente en `auth.users`.
- No retirar `EXECUTE` legacy hasta completar E2E autenticado, evidencia de rollback/cleanup y revalidación posterior.

## SECURITY · leaked password protection

Estado: `PARTIAL / HUMAN_REQUIRED: HIGH_RISK` por canal de escritura soportado ausente.

Evidencia de proveedor:
- Supabase documenta leaked-password protection en Auth para planes Pro y superiores.
- Supabase documenta gestión programática de Auth mediante `PATCH /v1/projects/{ref}/config/auth`.
- El conector Supabase disponible en este entorno no expone una acción de escritura de configuración Auth.

Decisión fail-closed:
- No usar PAT, Dashboard o navegador por fuera del canal autorizado para fabricar un verde.
- Mantener el warning abierto hasta disponer de un canal de configuración autorizado y auditable.

## RECOVERY · provider restore

Estado: `PARTIAL / HUMAN_REQUIRED: MONEY_LIMIT`.

Evidencia de proveedor:
- El inventario actual no ofrece un target aislado gratuito ya existente: proyecto principal con `main` solamente y proyecto legacy sin branches.
- Supabase documenta que `Restore to a New Project` crea un proyecto nuevo y genera gasto mensual adicional.
- PITR es un add-on de pago.
- La restauración sobre PROD se rechaza por riesgo de downtime y pérdida de datos.

Ya verde:
- Snapshot Git inmutable.
- Rebuild/recovery local y CI con SHA-256.
- Rollback real de código APP al anterior PROD `c7a15cff9a387f1f142c8eeb06fd83a799e85a61` ensayado sin despliegue en run `34808719859`.

Bloqueo restante:
- Restore aislado real del proveedor + integrity check + application smoke + cleanup/retention.
- Requiere `MONEY_LIMIT` si no aparece un target aislado de coste incremental 0 EUR.

## OBSERVABILITY · sink persistente 0 EUR

Estado: `PARTIAL`.

Evidencia Make:
- Make ya está conectado y en uso por Fénix.
- Data Store `171764` está compartido por CORE/deduplicación y por health snapshots PROD; YouTube escribe `HEALTH_YOUTUBE_CHANNEL` con `environment=PROD` y el monitor CORE consume/escribe configuración, DLQ y snapshots en el mismo store.
- Data Store `172319` pertenece a una auditoría temporal TEST de esquema y no es un sink PROD dedicado.
- Ninguno de estos stores está demostrado con el contrato obligatorio completo `company_id`, `engine_id`, `environment`, `version`, `kind`.
- El tool surface actual no expone una operación directa para crear/cambiar el schema de un Data Store aislado.
- Se intentó crear un escenario **inactivo y NO RUN** únicamente para validar compatibilidad del schema con esos cinco campos. Make rechazó la creación porque el módulo exige un Data Store precreado y el canal actual no puede crearlo. No se creó escenario y no se escribió ningún registro.

Decisión fail-closed:
- No reutilizar ni remodelar `171764`: hacerlo podría romper deduplicación/health existentes.
- No reciclar `172319` sin inventario, contrato y aislamiento.
- Mantener el sink JSONL LAB/CI verde, pero OBSERVABILITY PROD sigue abierto hasta demostrar almacenamiento persistente compatible y wiring paralelo sin romper lo existente.

## OBSERVABILITY · YouTube health

Estado: `PARTIAL / HUMAN_REQUIRED: HIGH_RISK` por credencial OAuth.

Evidencia live de Make:
- Escenario `9537666` (`FENIX · HEALTH · YouTube · Canal, vídeos y permisos · V1`) es read-only sobre YouTube y solo persiste health en Data Store.
- Se intentó activarlo para una ejecución controlada.
- Ejecución `a96383dd40b54b3c91688fe1039a84f4` falló antes de ejecutar módulos: Make no pudo verificar la conexión de YouTube y devolvió HTTP 400.
- La ejecución consumió `0 operations`, `0 credits` y no produjo escrituras.
- El escenario quedó inactivo/fail-closed.

Decisión:
- Se retira cualquier afirmación previa de `youtube_health_reauthorization_green` o `youtube_health_connection_rewired_green` como evidencia operativa actual.
- El siguiente gate es reautorización OAuth segura y nueva ejecución read-only verde; no se automatiza una reautorización de credenciales de una cuenta humana.

## FINOPS · importes actuales exactos

Estado: `PARTIAL`.

Evidencia:
- Existe referencia 2026 de Notion Business a 20 USD/miembro/mes, pero la propia ficha está `En progreso` y exige registrar factura real en EUR.
- No se ha encontrado importe exacto actual de factura Notion 2026.
- Existen avisos recientes de problema de facturación Google Cloud/Trading Lab, pero sin importe mensual exacto.

Decisión fail-closed:
- No estimar para convertir FINOPS en verde.
- El verde exige factura/ledger actual y atribuible.

## Regla de promoción

Mientras cualquiera de los grupos anteriores permanezca abierto:
- `automatic_prod_promotion_allowed = false`.
- No retirar privilegios legacy.
- No restaurar sobre PROD.
- No introducir nuevos costes sin `MONEY_LIMIT`.
- No considerar evidencia estructural como evidencia operativa.
