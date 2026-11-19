# CEREBRO · Auditoría persistente y preparación UMS-001 LAB

Base `0dfcac2272c84e551ec9d304a3839975928e767d`. Verificado el 19 de noviembre de 2026. No se volvió a ejecutar la sonda WIF ni se modificó su despliegue.

## Auditoría persistente

El plan Workers Free figura como plan activo a 0 USD en [Cloudflare](https://dash.cloudflare.com/e39a57e1ac42650ca5a6d5307cf0ac8e/workers/plans). Las 10 plazas D1 están en uso. Se desplegó un solo Worker privado y un Durable Object SQLite con jurisdicción UE. Web y previews deshabilitadas. El handler HTTP siempre devuelve 404. No se añadió plan, dominio, cron ni secreto.

- Worker `cerebro-knowledge-audit-lab`; versión `9cba282c-f3c4-424a-b7f0-ab3c332d2d7c`. El código y su configuración están en `knowledge_audit_lab`.
- La escritura física devolvió `INSERTED`; el reintento exacto devolvió `EXISTING` con la fecha original. Un intento de reutilizar el ID con datos diferentes y un campo de autorización fuera de esquema se rechazaron.
- Cloudflare registró el reinicio de la instancia y una lectura de la misma fila tras cambiar el identificador de arranque. Una segunda invocación de la cola confirmó de nuevo una sola fila y su fecha original. `runtime-evidence.json` conserva los dos identificadores de evento y traza observados.
- La fila contiene solo identificadores del ensayo, fecha, estado y SHA-256. No hay credenciales ni contenido del paquete. La pestaña Google `Auditoria` conserva la auditoría separada de Apps Script. El permiso de la cuenta lectora de Google sigue intacto. La ruta real de consumidores aún no escribe en este almacén.

### Reproducción y rollback

1. Confirmar que la cola LAB `cerebro-facebook-w24-read-canary-lab-eu` no tiene consumidor ni productor, y que se usa una ventana de prueba dedicada. Agregar temporalmente como único consumidor el Worker nuevo, con lote de 1.
2. Enviar el cuerpo JSON `{"type":"KNOWLEDGE_AUDIT_STORAGE_TEST","command":"WRITE_RESTART_READ"}` mediante la API autenticada de Cloudflare Queues. En Observability filtrar por `$metadata.service = cerebro-knowledge-audit-lab` y verificar `count=1`, `retry=EXISTING`, `before != after`, rechazo del conflicto y rechazo del campo ajeno. Tras la primera ejecución el resultado `first` puede ser `EXISTING`.
3. Enviar `{"type":"KNOWLEDGE_AUDIT_STORAGE_TEST","command":"VERIFY"}` y verificar la misma fecha de escritura. Retirar solo el consumidor nuevo tras confirmar la lectura. Estado final observado de la cola: 0 consumidores, 0 productores.
4. Mantener `workers_dev=false` y `preview_urls=false`. Para desactivar la prueba conservar el consumidor retirado. No eliminar el namespace; contiene el registro de verificación. El código versionado y los pasos anteriores permiten reconstruir el componente.

## UMS-001

Se verificaron `company_id=fenix`, `environment=LAB` y versión de motor `0.1.0` en la orden GitOps histórica y su manifiesto. Se registró la identidad de motor existente como un solo consumidor de evaluación, con ROLE, SPECIALIST y regla de procedencia/licencia del contrato creativo fijo 1.2.0. Se añadieron filas al final de las cinco pestañas; no se escribió en `Entregas_LAB`. El formato completo, procedencia, filas y resultado en vivo se incluyen en `ums001-receipt-queue.json`. Apps Script devolvió `LAB_BUNDLE_RESOLUTION_PASS` con 1.723 asignaciones a las 16:33:55 UTC. Se verificó en el panel el activador de tiempo `cerebroLabDrainIncremental`. La cuota UTC del 19/11 ya estaba en 600. El recibo queda sujeto al orden del lote y a la siguiente plaza disponible, sin adelantarse a los elementos existentes. El hash del archivo es una expectativa calculada con el resolver, no un recibo.

Para revertir el alta antes de emitir, contrastar el contenido con `ums001-receipt-queue.json` y limpiar el contenido de las cinco filas o tramos añadidos mediante una sola operación; preservar encabezados, filas restantes, disparadores e historial. Si ya existe un recibo, conservarlo como evidencia histórica.

## Gates todavía bloqueados

| Gate | Dependencia comprobada |
| --- | --- |
| Facebook E2E | `FB-00.SA-001` tiene recibo auténtico. El código del [SHADOW original](https://github.com/carlosjmunoz78/fenix-capital-cerebro-social/blob/ce38b7f5a3df23205d31e12f1aa05318947d461a/docs/FB00_SA001_RUNTIME_SHADOW_BRIDGE_20261118.md) ejecuta un fixture y carece de llamada a Gateway y de un emisor de identidad de máquina. Los bindings vivos confirman `SHADOW_ENABLED=false` y únicamente KV como almacenamiento. Debe existir una versión LAB del ejecutor con entrada de conocimiento autenticada. |
| UMS-001 E2E | El [emisor OIDC de medios](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43259579088) y el broker están acreditados para `IMAGE.SYNTHETIC`. El bridge y el broker tienen rutas de medios; el Preview de conocimiento presenta solo `/api/knowledge-lab` con principal de sonda fijo. Hacen falta el recibo de Apps Script y el vínculo del emisor real con un grant de conocimiento y una operación de evaluación sin generación. |
| Seguridad y rollback de agentes | Los dos ejecutores deben poder invocar una ruta de conocimiento de máquina por su propia identidad. Las negativas y el interruptor remoto se deben ejecutar sobre esa ruta; el ensayo de persistencia y la prueba previa de WIF no cubren ese gate. |

No se instalaron grants, se activaron procesos de imágenes, ni se modificaron Vercel, WIF, Workers existentes, App, CRM, DNS o PROD. PR #278 y #13 permanecen DRAFT.
