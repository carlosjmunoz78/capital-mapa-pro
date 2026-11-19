# KNOWLEDGE.READ · Preview personal LAB con Google WIF · 2026-11-19

## Verificación física

- Despliegue Vercel `dpl_8eUjQDzcu8xVdNqDgJy6fHrYCm2Y`, proyecto FACT-001 LAB `prj_LxPzJA5AkHJvhYzTAbVJbRrAvvLu`, equipo `team_qnh6u1Ofy2WPp0MGEKlyMA50`. Estado READY, target null (Preview), sin alias asignados. El intento sin sesión devolvió HTTP 302 a `vercel.com/sso-api`. El navegador del propietario pudo abrir la sonda privada.
- El uso de este Preview queda limitado al laboratorio personal no comercial del propietario. No se cambió el plan ni se añadieron productos de pago. Los despliegues de producción `dpl_AdnFjkCYenNU3e7fiAp6PgcoamcZ` y `dpl_DCk7j7wNbeaHmFc28CQ8b8DwHU9z` permanecen READY.
- FORGE usa el pool `knowledge-vercel-lab`, proveedor `preview`, issuer de equipo y condición de propietario, proyecto, entorno y subject exactos. Solo el principal Preview tiene el rol personalizado `knowledgeLabAccessToken` en la cuenta lectora de conocimiento. La función intercambia OIDC en Google STS y solicita un token de 600 segundos para `spreadsheets.readonly`. La hoja continúa privada y la cuenta conserva su permiso Lector. Ningún token se almacena.
- El primer HTTP 403 de IAM se resolvió tras propagarse la concesión. El test posterior devolvió `GOOGLE_WIF_VERIFIED` desde Vercel, sin utilizar las credenciales de Cloud Shell para Sheets.

| Comprobación | Resultado |
|---|---|
| Facebook | READ_VERIFIED · SHA-256 `0e3166ac244cf80290eb3242711d04260074f629d733d21673aeb57c6c044416` |
| Instagram | READ_VERIFIED · SHA-256 `66b8ee860a1d9a6508facf133aed201fbdf537541b7b4f59c5e8a9f1a46c886b` |
| LinkedIn | PENDING_RECEIPT |
| Negativas de identidad, empresa, versión y especialista | 4 denegadas |
| Interruptor local de la capacidad | disabled_check=true |
| Eventos de auditoría de la sonda | 7 |
| Agentes con consumo E2E | 0 |

El Preview sirve una sonda protegida que devuelve estados y huellas. La sonda autentica el workload de Vercel y usa alcances de prueba fijos. No concede acceso a agentes, no entrega paquetes a consumidores y no tiene auditoría duradera de producción. El apagado comprobado corresponde al binding de la sonda. Queda por probar un rollback remoto completo.

## Rollback y siguiente bloque

Deshabilitar únicamente el proveedor `preview` del pool `knowledge-vercel-lab` o retirar la concesión de su principal exacto en la cuenta lectora, sin tocar sus ACL de Sheets ni el pool GitHub. Los tokens ya emitidos caducan a los 600 segundos. Para producción de agentes en LAB, quedan la autenticación de consumidores reales y sus grants, la auditoría persistente, un tercer recibo auténtico y la prueba UMS-001 con un alcance y recibo acreditados. La cuota y el temporizador de Apps Script se conservaron. PR #278 sigue DRAFT.
