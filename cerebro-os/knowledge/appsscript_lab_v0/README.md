# KNOWLEDGE-FACTORY-001 · Apps Script y Google Sheets · LAB

## Estado y enlaces

- [Proyecto Google Apps Script](https://script.google.com/u/0/home/projects/1jR6GioO8BzbxhWYLoxKwMUQSqztAn4b2XKkLqT3ppuI8kS1XBU98-ZRv/edit) vinculado al [Google Sheet LAB](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit).
- [Entregas](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit#gid=815763748), [auditoría](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit#gid=1266644722) y [piloto](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit#gid=466573735).
- Facebook tiene 42 agentes principales, 527 especialistas, 527 asignaciones y 595 piezas de biblioteca. Los 22 lotes reales registraron 527 especialistas únicos con 527 hashes SHA-256. La repetición añadió cero filas.
- Último lote a las 2026-11-19T09:47:18.351Z. Hash del piloto `0e3166ac244cf80290eb3242711d04260074f629d733d21673aeb57c6c044416`.
- La cola temporal se encoló en Google y concluyó a las 2026-11-19T09:53:18.667Z con 527/527 al día y cero filas nuevas. El temporizador se retiró. Quedó un solo activador de edición.
- Consumo real por agentes, certificaciones y consultas autenticadas del Gateway verificados en esta sesión: 0. Coste adicional de infraestructura: 0 €.

## Contrato para registrar departamentos

1. En el mismo Sheet, crear `Departamentos` con cabecera `company_id, department_id, engine_id, environment` y una fila por ámbito autorizado LAB. Un `engine_id` identifica un solo departamento por empresa y entorno. Los registros históricos de Facebook siguen resolviendo con la configuración original.
2. Mantener la estructura de `Agentes`, `Especialistas` y `Biblioteca`. Añadir `engine_id`, `environment` y `department_id` al final de `Asignaciones`. Rellenar los tres en cada nueva asignación. Mantener vacías estas columnas en las asignaciones históricas compatibles de Facebook.
3. Cada especialista referencia su agente principal, su overlay y su versión. Las asignaciones referencian rol, overlay y reglas, con versión de paquete obligatoria. Las referencias pueden fijar una versión individual como `knowledge_id@version`. Reutilizar referencias comunes dentro de la misma empresa. Usar IDs distintos para recursos de departamentos que deban contener datos diferentes.
4. La biblioteca se resuelve por empresa, entorno, ID y versión. La procedencia es obligatoria. Las entregas quedan identificadas por empresa, entorno, especialista y hash del paquete, cuyo contenido incluye departamento, motor, agente y versión. Un hash nuevo crea un recibo nuevo. Las entregas históricas sirven como punto de reanudación.
5. Prueba reproducible con datos sintéticos: `node multiempresa-check.cjs`. Verifica dos empresas, tres departamentos, IDs coincidentes, selección de la biblioteca correcta y rechazo de una regla ausente aunque exista en otra empresa. El inventario operativo actual corresponde a Fénix Facebook.

## Operación, permisos y recuperación

- Permisos del manifiesto: `spreadsheets.currentonly` para esta hoja y `script.scriptapp` para gestionar sus activadores. El propietario autorizó ambos. El activador de edición se ejecuta con esa identidad.
- Editar las pestañas de entrada en Google Sheets encola una ejecución de un solo uso. Agrupar los cambios de un paquete antes de encolarlos. Las escrituras de conectores o API no generan eventos de edición en Google. Tras una importación API, abrir o recargar el Sheet y usar **CEREBRO · LAB → Encolar cambios de conocimiento LAB**. También puede llamarse `cerebroLabQueueIncremental` desde una integración autorizada que se ejecute dentro del proyecto vinculado. No hay un temporizador periódico de sondeo.
- El límite configurado es 25 entregas por ejecución y 600 por día UTC. El código impone máximos de 50 y 600. Los bloqueos documentales coordinan la cola y el bloqueo de script protege las entregas. Hay hasta tres intentos automáticos consecutivos. El temporizador de recuperación se retira al terminar y solo continúa si hay trabajo o una ejecución por recuperar.
- Si hay errores repetidos, inspeccionar **Apps Script → Ejecuciones**, corregir entradas y encolar de nuevo. Si la cuota diaria se alcanza con trabajo pendiente, la continuación se programa para después del próximo inicio de día UTC.
- Para detener la automatización, ejecutar `cerebroLabRemoveIncremental` desde la identidad que la instaló y verificar que se retiraron `cerebroLabOnKnowledgeEdit` y `cerebroLabDrainIncremental`. Las entregas conservan el punto de reanudación. Para restaurar el código previo al módulo incremental, usar `985bd15d519f95dd07c7998fbdd60e56eb75271f` y mantener deshabilitado el instalador de temporizador recurrente anterior. La restauración no se ejecutó en vivo.

## Gateway LAB · pendiente

El repositorio contiene el contrato `GatewayRequest`, el registro de conectores y el control de política, Supervisor y Tribunal. Falta acreditar una identidad del consumidor LAB con acceso a esta hoja y credencial de solo lectura `spreadsheets.readonly`. La autorización de Apps Script pertenece al propietario y la conexión de Drive utilizada para verificar recibos pertenece a esta sesión.

El adaptador privado debe aceptar la identidad autenticada y autorizada del consumidor, comprobar empresa y contexto LAB antes de leer, y devolver exclusivamente el paquete del ámbito solicitado con versión, procedencia y hash contrastado con su recibo. Parámetros: empresa, departamento, motor, agente, especialista, entorno y versión. Reutilizar los controles del Gateway y registrar evidencia. Gate mínimo: tres lecturas auténticas de especialistas y un rechazo de empresa ajena. Mantener desactivado `gateway_push_enabled`; no publicar una aplicación web.

## Huellas SHA-256 del código instalado

- `Code.gs`: `befa122e30c51554003680f0eb5c6941d6eea1a97fcee2a90aa8e15e2b22c5ae`
- `Incremental.gs`: `3ba8f0b7879ff7f62c8bc186360ae790afa9bf5516eaf965d0cfa0552b004f7b`
- `appsscript.json`: `db083eb105be3644f57cc38bc34b98f0ab0cdf47c4c87e7e58bc94e0b030453d`

Huellas sobre UTF-8 y saltos LF, normalizados al copiarlos desde el editor de Google.
