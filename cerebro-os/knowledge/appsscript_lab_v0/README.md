# KNOWLEDGE-FACTORY-001 · Google Apps Script + Sheets · LAB V0

**ESTADO: PREPARADO EN DRIVE Y GITHUB; NO INSTALADO TODAVÍA EN GOOGLE APPS SCRIPT; GATEWAY REAL NO CONECTADO.**

## Recursos físicos existentes
- Google Sheet LAB (real): https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit
- Google Drive CEREBRO: https://drive.google.com/drive/folders/1LwSuR6kshVN1I4m708dwIir50WzRQ4kx
- ZIP fuente y fixtures: https://drive.google.com/file/d/1ZzjFU69Jctj7pHL47Wwmv13iJPzuM8SR/view
- Origen inventario: Facebook PR #13, branch `cerebro/facebook-manual-knowledge-remediation-v1-20261118`.

La hoja tiene 42 roles, 527 especialistas, 527 asignaciones, 595 piezas de biblioteca y pestañas `Entregas_LAB`, `Auditoria` y `Piloto`.
El código está en `Code.gs` y usa un proyecto **enlazado al Sheet**, con permisos mínimos, sin HTTP, API de pago ni llamadas a Meta/App/CRM.
Tests Node con mocks de Apps Script: 527 resoluciones, 22 lotes, 0 agentes consumiendo el conocimiento, 0 certificados, 0 I/O externo, bloqueo por tenant.

## Para activar el script en Google (no lo hace la conexión actual de Drive)
1. Abrir el Google Sheet anterior. En **Extensiones > Apps Script**, crear proyecto enlazado a esa hoja.
2. Pegar el `Code.gs` versionado aquí y configurar `appsscript.json`.
3. Ejecutar `cerebroLabValidateAll` y autorizar solo el acceso requerido a Sheets; verificar 527/527.
4. Ejecutar `cerebroLabPilot` y luego `cerebroLabRunBatch`, confirmando recibos en la hoja.
5. La automatización recurrente **no se instala por defecto**: `Config!B8=FALSE`, `cerebroLabInstallTimedBatch` bloqueada.

## Puerta al Gateway real
El Gateway actual tiene un contrato de `GatewayRequest(company_id, engine_id, capability, environment, version)` y control de Supervisor/Tribunal.
Es obligatorio un lector **de solo lectura**, autenticado por OAuth, para recuperar por empresa/especialista y verificar integridad.
La interfaz de Google Drive conectada a ChatGPT **NO es una credencial del Gateway**.
El script no expone `doGet`/`doPost` ni publicación web bajo la cuenta propietaria. No hay derecho de producción, ni publicación, ni certificación.

**No fusionar ni instalar en PROD antes de:** autorización real, tests, costos medidos, OLD vs NEW, Supervisor, Tribunal, backup, rollback.
