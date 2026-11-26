# KNOWLEDGE.READ · evidencia física del binding privado · 2026-11-19

## Runtime e IAM

- En FORGE, el inventario de servicios de Cloud Run mostró únicamente `cerebro-advisory-preprod` en `europe-southwest1`. Ingress `internal`, revisión `cerebro-advisory-preprod-00264-dpv` con 100 % de tráfico, identidad `cerebro-forge-runtime@cerebro-forge.iam.gserviceaccount.com`. El inventario de trabajos estaba vacío. PREPROD queda fuera del ámbito LAB.
- El despliegue READY `dpl_AdnFjkCYenNU3e7fiAp6PgcoamcZ` en el proyecto Vercel `cerebro-fact001-vercel-lab-20261111`, región `iad1`, contiene `src/index.html` y `src/robots.txt`. No acredita una función Gateway ni una identidad consumidora allí. No se hizo un despliegue en Vercel ni se concedió acceso federado.
- La cuenta lectora de Google sigue habilitada, sin claves descargables. Su IAM mostró únicamente el permiso temporal del operador `projects/cerebro-forge/roles/knowledgeLabAccessToken`, con condición de expiración a las 11:57:01 UTC. No se amplió ni renovó. El probe obtuvo su token efímero de IAM Credentials, solicitando solamente `spreadsheets.readonly`, y lo conservó en memoria. El permiso preexistente sobre la hoja se usó con lecturas GET. Sin mutaciones IAM ni nuevos recursos facturables en esta ejecución.

## Contrato, registro y resultado

Ruta temporal en Cloud Shell de FORGE con `Gateway.route` y el registro Python existentes, binding Node `KNOWLEDGE.READ` y conector `KNOWLEDGE-GOOGLE-SHEETS-LAB-001`, autorizaciones exactas por las siete dimensiones y política limitada al probe. El probe no publica endpoint ni ejecuta Supervisor, Tribunal, identidad de agente ni auditoría de un runtime desplegado. No habilita el conector en ningún despliegue.

| Alcance | Resultado real de la sonda privada |
|---|---|
| Facebook, FB-00.SA-001 | READ_VERIFIED SHA-256 `0e3166ac244cf80290eb3242711d04260074f629d733d21673aeb57c6c044416` |
| Instagram, IG-00.SA-001 | READ_VERIFIED SHA-256 `66b8ee860a1d9a6508facf133aed201fbdf537541b7b4f59c5e8a9f1a46c886b` |
| LinkedIn, LI-00.SA-001 | PENDING_RECEIPT |
| SEO, SEO-D01:SPECIALIST:01 | PENDING_RECEIPT |
| Identidad ausente, empresa ajena, versión ajena, especialista no autorizado | Cuatro denegaciones antes del acceso a Google |
| Hash alterado en una copia en memoria de la respuesta auténtica | Fallo cerrado, hoja intacta |
| Credencial indisponible, Google HTTP 503, auditoría caída | Fallos inyectados y cierre seguro |
| Recuperación | Lectura repetida de Facebook tras retirar los fallos |
| Desactivación | `PROBE_DISABLED_NO_GOOGLE`, cero accesos a Google con el interruptor apagado |

Auditoría temporal: 12 eventos de 11:43:04.816 a 11:43:23.534 UTC, modo de archivo 0600. Cuatro DENIED, tres READ_VERIFIED (incluye recuperación de Facebook) y cinco FAILED. El intento con auditoría caída no emitió datos ni pudo escribir un evento. El proceso registró ocho pasos por el transporte, uno de ellos el 503 inyectado sin llamada a Google. Salida 2 por el tercer recibo aún pendiente. Dos ámbitos únicos verificados, cero lecturas de un runtime permanente, cero agentes con consumo demostrado y cero certificaciones.

## Cola, autonomía, dependencias y rollback

600 entregas en Sheet (Facebook 527, Instagram 73, LinkedIn 0, SEO 0), 1.122 pendientes. Activadores observados: `cerebroLabOnKnowledgeEdit` y un `cerebroLabDrainIncremental`. Continuación programada por la ejecución anterior para después de 00:01 UTC del 20 de noviembre. La cola, los recibos y los disparadores quedaron intactos.

Dependencias para cierre permanente: runtime LAB existente y autorizado con garantía de 0 € adicionales, identidad gestionada propia, permisos Google acotados a la cuenta y la hoja, autenticación real del consumidor, grants, Supervisor, Tribunal y auditoría persistente. Conservar política de mínimo privilegio y configurar límites de consultas antes de activación. Mantener el binding apagado por defecto. El lector de Apps Script y su automatización son independientes. Un agente de prueba concreto y autorizado debe ejecutar y registrar el consumo por Gateway después de un tercer recibo auténtico.

Rollback comprobado: interruptor de la sonda con cero peticiones. Rollback en runtime permanente pendiente al no haber despliegue. Eliminar solo la configuración del conector o revocar su concesión IAM específica al desplegarlo, preservando la auditoría. PREPROD y PROD intactos en esta ejecución.

Coste adicional de infraestructura: 0 € contratados, sin ampliación de facturación. Los límites existentes de la cola se conservaron. La prueba utilizó únicamente infraestructura ya disponible.

Changelog: `aab3164b2b5d11a6809fe506e7882d938e00c0e4` añade la prueba privada reproducible. Este documento registra la ejecución y el estado pendiente. PR #278 sigue en DRAFT.
