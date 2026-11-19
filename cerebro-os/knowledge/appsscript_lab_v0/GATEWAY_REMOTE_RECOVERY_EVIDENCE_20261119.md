# KNOWLEDGE.READ · apagado remoto y recuperación del Preview LAB

Evidencia registrada el 2026-11-19T13:25:03.853Z. Base: `66c7fd26526d4393487d3f3737cbf00bff1e0de2`. Alcance personal, privado y no comercial. [Preview protegido](https://cerebro-fact001-vercel-lab-20261111-d3ql8s3ps.vercel.app/api/knowledge-lab), despliegue `dpl_8eUjQDzcu8xVdNqDgJy6fHrYCm2Y`.

| Paso | Evidencia observada |
| --- | --- |
| Apagado | Google IAM confirmó `disabled: true` para el proveedor `preview` del pool `knowledge-vercel-lab` en `cerebro-forge`. |
| Nueva consulta con sesión Vercel autorizada | La misma sonda devolvió `GOOGLE_STS_HTTP_400` y no devolvió lecturas. |
| Restauración | IAM confirmó la actualización a habilitado. Una nueva petición al mismo Preview devolvió `GOOGLE_WIF_VERIFIED`. |
| Facebook tras restaurar | `READ_VERIFIED`, SHA-256 `0e3166ac244cf80290eb3242711d04260074f629d733d21673aeb57c6c044416`. |
| Instagram tras restaurar | `READ_VERIFIED`, SHA-256 `66b8ee860a1d9a6508facf133aed201fbdf537541b7b4f59c5e8a9f1a46c886b`. |
| Seguridad de la sonda | Cuatro denegaciones, `disabled_check: true`, siete eventos diagnósticos y `agent_consumption: 0`. |

Este rollback corta nuevas emisiones para el workload y restaura el servicio sin redesplegar. La revocación de tokens previamente emitidos y el interruptor remoto en una ruta de agentes siguen pendientes. El intercambio utiliza tokens de 600 segundos y no se capturó ni conservó ningún token.

## Consumidores y auditoría

- Facebook `FB-00.SA-001` tiene recibo auténtico y ejecutor determinista. El [puente privado SHADOW en PR #13](https://github.com/carlosjmunoz78/fenix-capital-cerebro-social/blob/ce38b7f5a3df23205d31e12f1aa05318947d461a/docs/FB00_SA001_RUNTIME_SHADOW_BRIDGE_20261118.md) usa la Queue y KV de su propio Worker, con evidencia anterior de ejecución SHADOW. El canal está sellado y carece de ruta y grant acreditados para el Preview Vercel. El acceso con sesión del propietario no autentica a ese especialista.
- UMS-001 cuenta con seis fuentes y 12 perfiles potenciales. El [consumidor FACT-OIDC-LAB-E2E-001](https://github.com/carlosjmunoz78/fenix-capital-inmo-map/blob/cerebro/ums001-private-ai-image-e2e-lab-20261112/cerebro/media-studio/v2/evidence/UMS001_CEREBRO_SHARED_GATEWAY_E2E_2026-11-12.json) está acreditado para medios LAB. Quedan pendientes el grant de conocimiento, la relación empresa/agente/versión autorizada y un recibo real de Apps Script. La política del registry de conocimiento aún no incluye UMS-001.
- El proyecto Vercel exacto tiene SSO en todos los despliegues y la API de conexiones devolvió una lista vacía. El binding exige un autenticador, registro de permisos y callback de auditoría confiables. No se acreditó almacenamiento durable autorizado accesible desde ese Preview. Google WIF conserva alcance de solo lectura. Los siete eventos de diagnóstico no prueban escritura y lectura durable, idempotencia ni persistencia entre despliegues. La ruta de consumo permanece sin activar.

## Google y continuidad

600 recibos únicos leídos directamente en [Entregas_LAB](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit): 527 Facebook, 73 Instagram, 0 LinkedIn, 0 SEO, 0 UMS-001. Pendientes 1.122 de las 1.722 asignaciones registradas. LinkedIn devolvió `PENDING_RECEIPT` y es un gate independiente. Triggers y recibos preservados.

Para desbloquear, hace falta un canal ya autorizado que autentique los principales de los ejecutores frente al Preview protegido y un almacenamiento LAB con escritura idempotente y lectura verificable desde el runtime. UMS requiere además el alta y un recibo auténtico para su ámbito exacto. Una vez registrados esos permisos mínimos, ejecutar decisiones LAB trazables desde los consumidores y comprobar la denegación remota de la capacidad. Sin cambios en PROD, Apps, CRM, Workers, DNS ni planes. Sin cargos nuevos contratados. Sin certificaciones.
