# NEWS-001 · Comprobación real DNS Brevo y estado MCP · 2026-11-17

## HECHO / auditoría Cloudflare SOLO LECTURA
- Cuenta: Cloudflare `e39a57e1ac42650ca5a6d5307cf0ac8e`.
- Zona activa: `fenixcapital.es` (zone id `a00ec81375b4acb02f9bd6e0fd64942f`), 33 DNS records en la lectura. No se ha efectuado ninguna mutación.
- Existen `brevo1._domainkey.fenixcapital.es` y `brevo2._domainkey.fenixcapital.es`, registros CNAME no proxied y destinos bajo `dkim.brevo.com`. Dos registros DKIM de Brevo ya configurados.
- Existe un TXT raíz de verificación Brevo, cuyo VALOR SECRETO/VALIDADOR no se reproduce en esta documentación.
- Existe exactamente un TXT `_dmarc.fenixcapital.es` con política `p=none` y `rua`. Preservar política y reportes existentes.
- El TXT SPF de correo transaccional está configurado para Hostinger/Hostinger Reach. Brevo no exige SPF ni MX para autenticación estándar del dominio (según documentación oficial). **No editar SPF**, no crear entradas duplicadas y no tocar MX.
- **No es prueba de que Brevo haya marcado el dominio como 'Authenticated'**: requiere lectura desde su panel/API autorizado. No prometer delivery a bandeja hasta correo de prueba y header DKIM pass.
- Documentación: https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC

## Acceso conector BREVO MCP
- Plugin privado creado y verificado: `plugins_6afcbfafb5c88191b4409e4fa4da9f1e`, versión 0.1.0, endpoint oficial `https://mcp.brevo.com/v1/brevo_lists/mcp`, modelo de autorización `Authorization: Bearer <MCP_TOKEN>` vía interfaz de conexión del usuario, nunca pegado en chat ni guardado en repo.
- Verificado 17/11: archivos válidos `mcp.json`/habilidad/plugin manifest; *no aparecen herramientas Brevo autenticadas en conversación*. Browser conectado general exige contexto de origen y Opera solo devuelve menú de Brevo, no contenido de listas. **MCP no conectado/certificado; inventario real de contactos aún pendiente**.
- Seguridad: la documentación oficial advierte que el token MCP puede otorgar acceso **completo de lectura/escritura** a la cuenta. El plugin solo limita por instrucciones la actuación a lectura, pero no constituye restricción técnica del token. Mantener envíos/comandos mutantes OFF y no declarar proxy "read-only" real hasta aplicarlo a nivel de servidor/API. Fuente https://developers.brevo.com/docs/integration-guide.
- Alternativa anterior conservada: script Python `brevo_inventory_readonly.py` con allowlist técnica GET y GitHub workflow privado, sin credencial real conectada, 19 tests PASS. No sustituir ni borrar.
- Cloudflare Workers AI usage read-only mostró `Neuronas utilizadas hoy 5.07k/10k` (panel 17-11-2026), pero todavía NO acredita plan ni tope de facturación. Modelos generativos pagos siguen bloqueados.

## Estado y próximos gates
`BREVO_DNS_RECORDS_PRESENT=PASS`
`BREVO_DOMAIN_PROVIDER_AUTH_STATUS=UNKNOWN`
`BREVO_EMAIL_DELIVERY_E2E=NOT_VERIFIED`
`BREVO_MCP_PLUGIN_CREATED=TRUE`
`BREVO_MCP_CONNECTED=NOT_VERIFIED`
`BREVO_LIST_DATA_NOT_ACCESSED=TRUE`
`NEWS001_CUSTOMER_SEND=OFF`
`NEWS001_PROD=HOLD`

Próximo acto operativo: el propietario conecta el MCP privado en ChatGPT (requiere acción explícita de autorización). Después listar solo agencias existentes en Brevo, remitente/domino/cupo real, conciliar consentimientos y bajas, hacer email de prueba al buzón autorizado; aprobar producción solo tras texto original real y QA UMS. No importar particulares históricos, no modificar DNS, CRM, App o WordPress.
