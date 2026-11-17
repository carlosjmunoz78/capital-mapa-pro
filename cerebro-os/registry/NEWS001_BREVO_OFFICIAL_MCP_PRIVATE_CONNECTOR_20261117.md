# NEWS-001 · Brevo MCP oficial · Conector privado CEREBRO · 2026-11-17

## HECHO
- Se ha creado plugin PRIVADO de usuario ChatGPT: `CEREBRO · Brevo Listas`, `plugins_6afcbfafb5c88191b4409e4fa4da9f1e`, versión `0.1.0`.
- URL de conexión: https://chatgpt.com/plugins/plugins_6afcbfafb5c88191b4409e4fa4da9f1e
- Source oficial Brevo: https://developers.brevo.com/docs/mcp-protocol. Endpoint existente oficial `https://mcp.brevo.com/v1/brevo_lists/mcp`; `streamable-http`, token **MCP** tipo Bearer, **sin token contenido en plugin ni repositorio**.
- Package privado creado mediante Plugin Creator y verificado con get_plugin_files: `plugin.json`, `mcp.json`, `skills/brevo-news001-readonly/SKILL.md` presentes y reconocidos; sin nuevo servidor/cloud/hoster/suscripción.
- La función inicial es revisión de listas y metadatos, no modificación ni campaña ni envíos. La habilidad de CEREBRO impide usar acciones mutantes aunque el MCP las exponga.
- Conexión de credenciales e instalación de plugin requieren **acción explícita del propietario** en la interfaz de ChatGPT y Brevo; todavía **NO AUTENTICADO/NO VERIFICADO E2E**.
- No exponer token en conversación, GitHub, Supabase, WordPress, logs o artefactos. Brevo instruye: Account → SMTP & API → API Keys → Generar token marcando **MCP**, luego autorizar dentro del plugin. No afirmar que una clave API v3 ordinaria equivale al token MCP.
- Antigua ruta determinista offline de inventario vía API REST y su CI siguen preservadas como fallback; no borrar ni reemplazar. Run 44170335584: 19/19 PASS, sin datos de clientes. Workflow privado `news001-brevo-inventory-readonly-lab.yml` listo para uso futuro de credencial `BREVO_API_KEY` si se necesitase, pero no ejecutado contra proveedor.
- Staging Cowboy MCP conectado presenta error interno en discover, por tanto NO se usó para modificar WordPress. Formulario PROD y CRM permanecen intactos.

## NEXT BLOCK
1. El propietario abre el plugin privado y conecta una credencial MCP Brevo mediante pantalla de integración, sin compartirla en chat.
2. Comprobar que aparecen las herramientas del MCP para listar LISTAS (solo lectura). Buscar listas de inmobiliarias y sus IDs, sin confundir PREPROD con PROD, y verificar sus miembros/opt-out/consentimiento con evidencia previa a cualquier envío. Particular antiguo en Brevo queda fuera por política.
3. Certificar un remitente y dominio de Brevo y cuota real de Free. Si el MCP de listas no permite leer remitente/plan, ampliar el plugin por versión a las herramientas oficiales `senders`/`accounts` sin introducir servidores propios.
4. NEWS-001 editorial IA, Productora UMS-001 QA, formulario de consentimiento con backup y rollback, DOI/bienvenida. Solo test a buzón autorizado. Envíos comerciales siguen OFF.

## Estado exacto
`BREVO_MCP_PRIVATE_PLUGIN=CREATED_AND_FILES_VERIFIED`
`BREVO_MCP_AUTHENTICATION=PENDING_USER_CONNECTION`
`BREVO_MCP_LIST_DATA=NOT_READ`
`BREVO_CONTACT_MUTATION=NONE`
`BREVO_CAMPAIGN_SEND=OFF`
`ADDITIONAL_PAID_SERVICES=NONE`
`NEWS001_PROD=HOLD`
