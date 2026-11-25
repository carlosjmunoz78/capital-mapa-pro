# FACT-001 · Gate real multiempresa, cadena de identificadores y runtime P5 · 19/11/2026

**Ámbito:** read-only Cloudflare LAB EU, código FACT candidato DRAFT. **Sin cambios en Workers, colas ni credenciales.**

## 1. Ejecución REAL de FACT Recovery/P5 en D1 Cloudflare

Cuenta: `e39a57e1ac42650ca5a6d5307cf0ac8e`. Worker `cerebro-fact001-recovery-runner-lab` con Cron `*/5 * * * *`, sin ruta pública de ejecución. Base D1 `cerebro-fact001-recovery-lab-eu` (`1305f791-7c44-47f9-946b-f330a09c88aa`), consultada mediante SELECT agregado, sin payloads ni modificaciones.

| Origen | Lectura física |
|---|---|
| `fact001_runner_ticks_v1` | 2.548 ticks; 2.545 `EMPTY`, 3 `COMPLETED`; última observación 19/11 06:05:44 UTC |
| `fact001_runner_jobs_v1` | 3 trabajos `COMPLETED` históricos |
| `fact001_p5_jobs_v1` | 8 `COMPLETED` y 1 `RECONCILE` histórico; último completado 19/11 00:00:48 UTC |
| `fact001_p5_audit_v1` | 9 `QUEUED`, 8 `RUNNING`, 8 `COMPLETED`, 1 `RECONCILE` |
| `fact001_p5_automation_registry_v1` | ejecución registrada `providers.five.inventory.read`, `max_daily_jobs=1`, `enabled=1`, `max_cost_eur=0` en jobs |

**Interpretación estricta:** hay actividad real y recurrente en el motor P5 (lecturas de inventario de proveedores), NO fabricación de nuevos motores ni 2.548 tareas comerciales ejecutadas. Un tick `EMPTY` significa que la cola no tenía trabajo. `max_cost_eur=0` es un límite declarado, no verificación de factura.

## 2. Conflicto de identidad de empresa

- Registro canónico EXISTENTE `cerebro-os/config/improvement_companies.lab.json` incorpora `company_id=fenix` con `legal_name=Fenix Capital`.
- D1 P5 `fact001_p5_jobs_v1` y `fact001_p5_automation_registry_v1` utilizan `company_id=fenix-capital`.
- **No existe aquí una prueba de equivalencia certificada:** estas ejecuciones no pueden contarse automáticamente como realizadas por una entidad canónica `fenix` hasta registrar un contrato de alias con origen, validez, permisos y tribunal.
- Nueva puerta `auditCompanyScope('fenix','fenix-capital')`: `HOLD_COMPANY_ID_MISMATCH`, sin atribución ni ejecución cruzada. Si las IDs coinciden, tampoco se amplían permisos entre empresas.

## 3. Cadena FACT→UMS: no solo dos Workers

Auditoría read-only de los 23 Workers cuyo nombre contiene `fact001` o `ums001`. **8 Workers LAB** tienen en conjunto **13 expresiones** de identificador con la regla estricta `^[A-Z][A-Z0-9-]{2,63}$`:

| Worker LAB | Sitios |
|---|---:|
| `cerebro-fact001-gateway-lab-eu-20261109` | 3 |
| `cerebro-fact001-github-oidc-enroll-lab-eu` | 1 |
| `cerebro-fact001-ums001-issuer-provisioner-lab-eu` | 1 |
| `cerebro-ums001-registered-image-executor-lab-eu` | 1 |
| `cerebro-ums001-universal-engine-adapter-lab-eu` | 1 |
| `cerebro-ums001-universal-gateway-lab-eu` | 3 |
| `cerebro-ums001-universal-router-lab-eu` | 2 |
| `cerebro-ums001-universal-runtime-broker-lab-eu` | 1 |

Algunas validaciones son **de runtime_id y no de engine_id**, por lo que sustituirlas en masa podría crear una vulnerabilidad IAM. La migración debe identificar sus campos y relaciones individuales y preservar validación de runtime, anti-replay, firma, scope de empresa y permisos de publicación.

- Nueva puerta de código puro `fact001_full_cloud_id_chain_preflight.mjs`: exige 8 fuentes y 13 sitios observados, bloquea drift y cualquier plan parcial de dos Workers. Ejecutada sobre el Git blob exacto, con **7 grupos de verificaciones correctos**, sin cambios Cloudflare.
- Pruebas en `tests/fact001_full_cloud_id_chain_preflight.test.mjs`: contrato 8/13, denegación incompleta, drift, compañía `fenix` vs `fenix-capital`, atributos no autorizados. Suite Node preparada; no afirmar que GitHub Actions la ha ejecutado.

## 4. Autenticación existente: NO degradar

- Altas históricas FACT→UMS de 12/11 verificadas en Cloudflare Vault como `ACTIVE` con clave privada cifrada, para `FACT-OIDC-LAB-E2E-001` y `FACT-OIDC-CANARY-20261112`.
- El puente OIDC exige JWT real de un workflow GitHub autorizado. **No hay nuevo alta OIDC comprobada sin GitHub Actions**.
- El provisionador exige firma HMAC y controla empresa/capacidad; se conserva. No se exportan secretos ni se envía solicitud usando credenciales de dueño.
- La corrección Python de `3RD-001` mantiene `HOLD_CLOUD_PROVISIONER_ID_SCOPE` mientras la cadena completa no esté certificada.
- `UMS-001` rechazo histórico `CREATIVE_REJECTED_BY_OWNER` permanece sin reactivación. Ninguna imagen generada ni publicación autorizada por este cambio.

## 5. Backup, rollback y costes

- Snapshot no secreto del deployment/version ID y tipos de bindings de los dos Workers iniciales: `FACT001_CF_WORKER_DEPLOYMENT_POINTER_SNAPSHOT_LAB_2026-11-19.json`. **No sustituye un backup cifrado de código/configuración**, ni prueba rollback físico.
- Código y pruebas en PR #277 DRAFT; la rama `cerebro-engine-factory-v0` y producción siguen intactas. Rollback de esta fase = descartar PR sin hacer merge.
- El panel OPERATIVA dispone de lector agregado D1 opcional con bandera `CEREBRO_CF_D1_READ_ENABLED` **OFF** por defecto; no llamar al endpoint repetidamente si el token actual no está acreditado para D1 Query. Los resultados anteriores sí se verificaron con la conexión administrativa Cloudflare de solo lectura.
- Suscripciones nuevas: 0 €. Coste marginal de CPU/Workers/D1/Cloudflare y Vercel: **no medido**.

## Próximos gates

1. Contrato documentado de alias `fenix` vs `fenix-capital` o mantener ámbitos explícitamente separados.
2. Aislar en PREPROD los 8 Workers y sus 13 sitios: distinguir engine_id de runtime_id y probar rechazos.
3. Obtener identidad real de runtime que no supla GitHub OIDC ni debilite el provisionador; enviar canary legítimo solo tras permisos.
4. Backup cifrado y restauración probada, OLD vs NEW, coste y tribunal; promover gradualmente solo si todas las puertas están verdes.

**Estado: FACT P5 lector programado VERIFICADO LAB; FACT generador Python PROBADO LAB; cadena IAM alternativa NO CERTIFICADA; PROD=HOLD.**

## CP141 — 24/11/2026 · Candidata completa de cadena de identidad

Se amplía el preflight existente, sin modificar su contrato anterior ni desplegar Workers. GET de las ocho fuentes LAB reales: 13 sitios clasificados, 12 de engine_id (incluidos dos validadores compartidos de issuer cuyo contrato exige issuer.origin_engine_id igual al emisor firmado y al origin_engine_id) y uno estrictamente runtimeId que se conserva. planClassifiedCloudIdChainMigration exige los ocho Workers, cuenta original exacta y campos/calls observados, preserva igualdad de issuer y runtimeId, prueba roundtrip exacto de cada fuente, y devuelve candidata sin autorización de despliegue. La transformación se ejecutó en memoria contra las ocho fuentes reales, únicamente GET, sin exportar código o secretos; 12 cambios de regex previstos, 1 conservado, 8/8 roundtrip exacto. Fixtures locales: 12/12 tests, 177/177 IDs aceptados, incluido 3RD-001, malformed/drift/issuer/runtime rechazados. Log SHA256 507312d4e8da17c57951ddf111a59d4ebe9cfbda64ebe81119ae6c97fbd980a6. No equivale a alta firmada, backup o rollback de despliegue. No cambiar guard Python HOLD_CLOUD_PROVISIONER_ID_SCOPE ni alias empresa hasta certificar en LAB versiones exactas, firmas, aislamiento, coste, rollback y tribunal. No nuevo Worker, cola, suscripción ni modificación cloud/PROD. El plan de sustitución solo es candidato textual; revisión semántica y prueba de runtime siguen obligatorias.
