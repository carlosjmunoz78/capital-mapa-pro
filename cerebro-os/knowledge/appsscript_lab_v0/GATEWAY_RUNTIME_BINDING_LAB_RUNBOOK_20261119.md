# CEREBRO OS · KNOWLEDGE-FACTORY-001 · Gateway LAB de lectura privada · Runbook V1

**Fecha:** 2026-11-19 · **Estado:** ADAPTADOR Y CONTRATO DE ENLACE IMPLEMENTADOS EN PR #278 DRAFT / NO DESPLEGADOS EN RUNTIME REAL.

**No equivale a 3 lecturas E2E reales, autorización de agentes, formación profesional ni certificación.**

**Actualización:** el binding se ejecutó de forma privada en Cloud Shell con 2 lecturas reales respaldadas por recibos, denegaciones y desactivación verificadas. Falta un runtime LAB elegible e identidad permanente. Véase [evidencia física y rollback](GATEWAY_RUNTIME_BINDING_LIVE_EVIDENCE_20261119.md).

## 1. Evidencia real existente

| Elemento | Evidencia | Estado |
|---|---|---|
| Google Sheet principal | `1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc` | REAL, PRIVADO, LAB |
| Google Apps Script vinculado | `1jR6GioO8BzbxhWYLoxKwMUQSqztAn4b2XKkLqT3ppuI8kS1XBU98-ZRv` | REAL, OAuth concedido |
| Inventario | Facebook 527; Instagram 527; LinkedIn 527; SEO 141 | 1.722 asignaciones |
| Recibos 19/11 | Facebook 527, Instagram 73, LinkedIn 0, SEO 0 | **600 únicos reales, 1.122 pendientes** |
| Cuota de seguridad | `Config.max_daily_rows = 600`, ejecutor de lotes y cursor | REAL, límite interno, no cuota oficial de Google |
| Continuación | Un trigger `cerebroLabDrainIncremental` para 20/11 tras 00:00 UTC | Declarado por Work; comprobar en los registros posteriores |
| Capacidad física | `Entregas_LAB` ampliada de 1.200 a 5.000 filas | CAMBIO REVISADO / confirmado Google API |
| Google principal | `cerebro-forge` | GCP FORGE |
| Cuenta lectora dedicada | `cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com` | REAL, lector en esa hoja según evidencia Work |
| APIs | Sheets API e IAM Credentials API habilitadas en FORGE | Informado por Work |
| OAuth operador | Impersonación temporal, expiró 2026-11-19 11:57:01 UTC | **NO sustituye identidad de runtime permanente** |
| Canario GCP real | Facebook e Instagram validaron hash; compañía ajena y versión ajena rechazadas | **2 / 3 lecturas REALES; tercera pendiente** |
| Consumo real de agentes | Ninguno demostrado | **0** |
| Certificaciones profesionales | Ninguna | **0** |

Fuentes existentes: `EVIDENCE_CLOSURE_INCREMENTAL_20261119.md`, `GATEWAY_SHEETS_LAB.md`, `gateway_sheets_probe.cjs`, `gateway_sheets_lab.cjs` y las pestañas `Entregas_LAB` y `Auditoria` de Google Sheets.

## 2. Implementación aditiva en esta PR DRAFT

No se modificaron `Code.gs`, `Incremental.gs`, `gateway_sheets_lab.cjs`, `service.py` ni `registry.py` originales.

- `gateway_runtime_lab_binding.cjs`: crea un lector de la capacidad `KNOWLEDGE.READ` usando el adaptador de Sheets previamente acreditado. Sin endpoint HTTP y **OFF por defecto**. Acepta únicamente el contexto verificado del runtime, grants de un registro seguro, `Gateway.route` autenticado, decisión `policyCheck === true`, token Google efímero y escritura obligatoria de auditoría. La autorización rechaza empresa, motor, entorno, departamento, agente, subagente y versión ajenos. No permite PROD.
- `createGoogleManagedReaderTokenProvider`: opción **keyless** para ejecución en un runtime ya hospedado en Google, con la cuenta lectora asignada como identidad del proceso. Compara el email de identidad del servicio de metadatos de Google. No usa claves JSON ni el OAuth temporal del operador. El token gestionado podría tener scopes de plataforma amplios; el permiso efectivo sobre Drive DEBE restringirse a lector de la hoja privada y los únicos accesos al API son `GET`.
- `gateway_runtime_lab_binding_check.cjs`: prueba LOCAL con **tres datos sintéticos** Facebook, Instagram y LinkedIn, verificando contrato, hash, origen de grants, rechazo de empresa y versión ajenas, denegación de PROD, política, rutas y fallos de auditoría, sin acceso Google ni coste.
- `cerebro-os/gateway/knowledge_read_lab_registry.py`: declara capacidad y registro explícito en el `Gateway` Python existente, por empresa y motor, únicamente LAB y **sin registro activo por defecto**. `fenix` y `fenix-capital` no se fusionan. `ROUTED` no implica consumo real. No modifica el Gateway original ni lo desplegado.
- `cerebro-os/tests/test_knowledge_read_lab_registry.py`: cuatro pruebas locales de ruta, aislamiento y denegación, reutilizando `GatewayRequest`, `Gateway` y `ConnectorRegistry` originales.

`KNOWLEDGE.READ` debe enlazarse con su conector privado **únicamente tras comprobar identidad real, permisos mínimos y auditoría persistente**. No reutilizar las credenciales de la conexión de ChatGPT normal ni las del editor Apps Script como identidad de Gateway.

## 3. Procedimiento de activación física sin nuevos servicios

**GATE A · Seleccionar un runtime LAB EXISTENTE con identidad gestionada.** Verificar cuál es el runtime real autorizado para alojar el adaptador. El repositorio tiene un Gateway Python de contratos y un Gateway compartido de UMS-001 en Cloudflare; ninguno es evidencia de que el lector Google ya esté hospedado. **No crear Cloud Run, Workers, servidores, proyectos ni servicios de pago automáticamente.** Si no existe runtime apto, `BLOCKED_RUNTIME_HOST_UNVERIFIED`.

**GATE B · Identidad permanente.** En un runtime Google ya existente y autorizado, vincular la cuenta `cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com` como identidad gestionada de dicho runtime, sin generar claves. Si el runtime usa otra identidad, exigir federación/impersonación controlada con permisos exclusivos para esa cuenta y alcance limitado; no reutilizar la concesión temporal del operador. Comprobar que el runtime no puede acceder a otras carpetas ni hojas ni escribir en la hoja. No registrar ni imprimir tokens.

**GATE C · Autorización de consumidores.** El servidor ya autenticado debe proporcionar cinco dependencias inyectadas: `authenticateRuntime`, `readTrustedGrants` del registro IAM real, `routeGateway` mediante `Gateway.route` existente, `policyCheck` sin excepciones automáticas y `persistAudit` en almacenamiento duradero ya contratado. Un sexto callback `googleAccessToken` deriva token efímero de la identidad del runtime. La solicitud externa NO puede proporcionar su propio usuario, grants o credenciales. Rechazo previo al acceso a Google.

**GATE D · Ruta.** Registrarse en `ConnectorRegistry` exclusivamente como `KNOWLEDGE-GOOGLE-SHEETS-LAB-001`, `KNOWLEDGE.READ`, `OFFICIAL_API`, `environment=LAB`, con tenants explícitos y motor vinculado. Los tenants `fenix-capital` y `fenix` son distintos mientras no exista contrato de identidad. Mantener `enabled=false` hasta completar A/B/C. No registrar comodín global ni capacidad PROD.

**GATE E · Test real de consumo.** Tras recibir un recibo en LinkedIn (o SEO) por el temporizador de Google y tener identidad de runtime permanente, obtener **tres lecturas desde el runtime** (Facebook, Instagram, LinkedIn o SEO) con hashes coincidentes. También demostrar que empresa ajena, versión ajena, falta de recibo, token inválido y auditoría caída rechazan la consulta. Registrar evidencia con `consumer_id`, ámbito, resultado y hash, sin contenido privado.

**GATE F · Agente consumidor real.** Solo ahora conectar un agente LAB autenticado concreto a la capacidad (no una sonda ni el navegador del operador). Evaluar exactitud, uso, cambios OLD vs NEW, políticas y Tribunal. Distinguir `GATEWAY_LAB_READ_VERIFIED` de `AGENT_CONSUMED_KNOWLEDGE`, y esto último de `CERTIFIED`.

## 4. Pruebas y verificación de código

Dentro de la rama PR #278, con Node.js 20+ y Python 3:

```bash
cd cerebro-os/knowledge/appsscript_lab_v0
node gateway_sheets_check.cjs
node gateway_runtime_lab_binding_check.cjs
cd ../../
python -m unittest discover -s tests -p 'test_knowledge_read_lab_registry.py' -v
```

Resultados de ejecución **local aislada**, antes de subir este paquete: prueba existente del adaptador PASS, nuevo canario de tres alcances sintéticos PASS, cuatro pruebas Python PASS. No realizar llamadas Google en estos tests. No son una prueba de despliegue vivo.

Resolver Apps Script PINNED SHA-256 de `Code.gs`: `befa122e30c51554003680f0eb5c6941d6eea1a97fcee2a90aa8e15e2b22c5ae`. Si cambia la implementación, hay que sincronizar el proyecto de Google, regenerar el hash y modificar a la vez `pinnedResolver` del lector. Las pruebas de alcance anteriores deben repetirse antes de activar.

## 5. Continuidad, costes, rollback y prohibiciones

- **Continuidad:** comprobar registros la mañana del 20/11. Estimación si funciona 600/día: total 1.200/1.722 el 20/11 y 1.722/1.722 el 21/11. No declarar realizado hasta leer recibos.
- **Coste:** no se han contratado servicios, generado tokens de pago ni creado infraestructura en esta ampliación. **0 € adicionales contratados**, no afirmar factura cero de recursos existentes sin Billing.
- **Rollback de código:** revertir únicamente commit del binding en la PR DRAFT. El Gateway, la productora, el Google Apps Script y producción siguen intactos.
- **Rollback de acceso:** desactivar la capacidad, revocar grants específicos del runtime (no los del propietario), y verificar que futuras lecturas fallan. Guardar audit, no eliminar evidencia.
- **Seguridad:** no publicar web app Apps Script; no nuevos Worker Cloudflare; no GitHub Actions; no claves estáticas; no escritura CRM/App/Supabase PROD; no Trading; no merges; no promociones; no costes sin autorización.
- **Rendimiento:** el lector V0 obtiene los siete rangos completos de Google Sheets en cada consulta. Antes de alto volumen, medir latencia/cuotas y añadir caché privada con TTL y versión si es necesario, sin contaminar tenants. No anunciar reducción medida de carga Cloudflare sin datos.

## 6. Estado de entrega de esta versión

- **HECHO:** binding Node LAB privado OFF por defecto, ruta LAB Python condicionada, tests locales, runbook y evidencia versionada.
- **EXISTENTE:** servicio Google lector, hoja y Apps Script, 600 entregas LAB, 2 lecturas reales de la sonda y negativas de alcance.
- **BLOQUEADO PARA CIERRE E2E:** falta runtime LAB con identidad permanente, binding físicamente desplegado e identidad de agente consumidor; tercera lectura real depende de nuevo recibo.
- **NO DECLARAR:** E2E real Gateway, especialistas formados, certificación, uso real por agentes, migración de producción ni reducción medida de Cloudflare.