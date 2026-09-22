# Browser Operator · Cloud ACK / Lease Alignment · 2026-09-22

## Evidencia verificada
- v1.6.2 físico: Bridge 1.4.1 GREEN, extensión 1.6.2 CONNECTED, mismo `lab-0b01ecef4d3d44918d93d3a0aa9d699e` en pestaña local y `COMPLETED / LOCAL_TEST_PAGE_OPENED`; ACK local en 80 segundos.
- Cloud preflight `browser-v162-cloud-preflight-20260922-1753`: COMPLETED, `semantic_verified=true`, 1 delivery, payload `ACCESSBOOT_CAPABILITY_SNAPSHOT`.
- Primera apertura cloud real `browser-v162-cloud-open-20260922-1854`: `COMPLETED`, `semantic_verified=true`, result `LOCAL_TEST_PAGE_OPENED`, **2 delivery attempts** (18:53:31 y 18:56:15 UTC). Solo una orden cloud insertada. El recibo no incluye recuento de pestañas; no afirmar deduplicación física medida.
- Durante la espera, v5 tiene lease 90 s y el transporte instalado timeout local 60 iteraciones; la acción física reciente había tardado 80 s. El polling recuperó el lease y finalizó el mismo `command_id` al segundo intento. Esto demuestra recuperación; también justifica alinear timeouts para eliminar el reintento evitable.

## Estado
HECHO: circuito cloud real PREPROD → PC → confirmación PREPROD; mismo command_id cloud, 2 delivery attempts, resultado semántico positivo. HECHO: alcance fenix/LAB/v0, sin mutación externa.
DEFINIDO: transporte alternativo v1.4.3 con reloj monotónico límite 170 s; gateway PREPROD v6 con lease 240 s. Archivos **paralelos**, no desplegados.
POR AUDITAR: reinicio de worker durante acción y ledger pendiente CLAIMED, conservación efectiva de pestaña única tras replay, recuperación de transporte intermitente. No autorizada operación autónoma PROD.

## Dependencias / contrato
- Bridge local 1.4.1 caduca una orden no terminal a 180 s; extensión 1.6.2 conserva recibos multi-ID fail-closed.
- Transporte en PC usa protocolo 1.4.1 y credencial DPAPI existente; el archivo v143 mantiene ese protocolo y el mutex único.
- Gateway en Supabase `hnqlnvakzaywtafeiybt` versión **v5 en vivo**; v6 es un archivo de código paralelo, NO desplegar independientemente del upgrade de transporte o mientras haya comandos QUEUED/DELIVERED.
- Nunca modificar / borrar secretos, emparejamientos ni la extensión ya conectada; snapshot y rollback íntegro; no tocar PROD, CRM, App ni WordPress.
- Esperar `QUEUED=0,DELIVERED=0`, snapshot v5 y logs, ensayar v143+v6 en PREPROD simulado con ACK a 80, 160, 170, caída de worker, expiración de lease, ACK duplicado y reenvío A→B→A antes de promoción.
- Después crear paquete reversible específico para transporte; verificar PS5.1 ejecución real en CI y PREPROD, hash payload y rollback, y solo entonces instalar con acceso local documentado.
- No existe capacidad autorizada de suspender Windows en el Gateway actual. No inventar comandos de sistema ni ampliar el permiso de acciones para conseguirlo.

## Rollback
Hasta promoción: revertir esta rama / no deploy; el Bridge v1.6.2 instalado y gateway v5 siguen intactos.
Después de promoción piloto: backup byte-a-byte del transporte instalado, snapshot función v5, prueba de vuelta a credencial y extensión previas; rollback ante fallo health, heartbeat, nonce, result conflict o lease/replay.
