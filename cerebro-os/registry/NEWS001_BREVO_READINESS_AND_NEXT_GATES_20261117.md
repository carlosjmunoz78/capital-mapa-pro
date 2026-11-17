# CEREBRO NEWS-001 · Brevo Free · Continuidad tras ejecución 17/11/2026

## Objetivo definido
Dos newsletters editoriales realmente nuevas, B2B inmobiliarias ya existentes en Brevo y B2C exclusivamente leads futuros de Fénix CEREBRO Leads (a partir de la fecha efectiva de activación). Productora UMS-001 con control visual independiente. Bienvenidas y envíos escalonados a través de Brevo Free; coste adicional cero.

## Verificado en sistemas vivos / HECHO
- Browser Brevo conectado: UI de contactos muestra 87 registros globales en conjunto, incluyendo registros QA; se conoce por notificaciones que existe lista histórica `[24] FENIX PREPROD · Inmobiliarias`. **No se certificó el número exacto de agencias en esa lista ni consentimiento comercial de cada una.** No hubo cambios ni envío Brevo.
- WordPress PROD: plugin activo `Fénix CEREBRO Leads 1.3.6-preprod`, leído vía Cowboy MCP, fuente 18.636 caracteres, fecha de archivo 2026-09-30. Contenía `!empty($data['consent_marketing'])`, que trata el string `"false"` como verdadero, y dos cargas JS `consent_marketing:false`. Modal propio no tenía casilla separada de newsletter. No cambiar WordPress PROD sin backup/QA/rollback.
- Supabase PROD `cluhljgonannaafpmblx`: Edge function `fenix-web-lead` v5 ACTIVE delega a `fenix_prod_web_lead_ingest_guarded_server` y `fenix_prod_web_lead_ingest_server`; inserta en `fenix_prod.clientes` y eventos. CRM real (consultas SELECT agregadas, sin exponer PII): `fenix_prod.inmobiliarias`: 401 en tabla, 18 agencias activas reales, 16 activas con email, **0** de esas con `consentimiento_marketing_b2b=true`; `fenix_prod.clientes`: 93 activos reales, 41 con email, 2 con `canal_entrada='Web'` y email, ambos `consentimiento_comercial=false`. **No confundir CRM con Brevo**, ni estos indicadores faltantes con prueba de que alguien rechazara expresamente las newsletters.
- Nuevo candidato de plugin completo y snapshot exacto en `cerebro-os/engines/CEREBRO-NEWS-001/wp-leads-lab/`. El candidato interpreta marketing consent con boolean estricto; captura un checkbox explícito para los formularios que lo tengan, añade casilla separada opcional a modal propio y reconoce field newsletter de Elementor. No considera checkbox de privacidad como marketing; rest endpoint original y estructura de payload intactos. GitHub CI [run 44158701213](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/44158701213) GREEN: PHP syntax + pruebas de regresión. Commit `68a7ee7abb0753c640a0adbdf620c3b0607028e4`.
- Planificador determinista `brevo_free_daily_planner.py` y su batería de 21 pruebas en `cerebro-os/tests/test_news001_brevo_free_daily_planner.py` GREEN por GitHub CI [run 44159151476](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/44159151476). Commit `ac38d86a5e11c84c45cfed9a7c226a0543828daa`. **No envía nada.** Requiere cuota verificada en cuenta, filtra solo contactos con cohort guard válido, comprobación editorial/visual, supresiones, duplicados y prioridades; cap de diseño <= 300/día.
- Documentación oficial Brevo actual: Free 300 emails/día, límite reinicia diario, no acumula envíos; campaña >300 alcanza 300 el día programado y requiere requeue por restantes. Hasta 2000 contactos únicos de automatización. DOI oficial `POST /v3/contacts/doubleOptinConfirmation` exige lista, plantilla DOI y URL de redirección (sin usar secretos en chat). Fuentes: https://help.brevo.com/hc/es/articles/208580669-FAQ-Cu%C3%A1les-son-los-l%C3%ADmites-del-plan-Gratis y https://developers.brevo.com/reference/create-doi-contact
- NEWS-001 DeepSeek redacción original real todavía NOT_PROVEN, dos imágenes UMS-001 rechazadas VISUAL_QA, Brevo SEND OFF y CRM/App/WordPress PROD protegidos.

## Pendientes exactos y orden de cierre
1. Inventario Brevo real por API (solo lectura) o Work browser autorizado: listas y sus IDs reales, contactos agencias elegibles, remitente/domain SPF/DKIM/DMARC, bajas/rebotes, plantillas DOI/bienvenida, métricas/free daily remaining. No utilizar lista PREPROD como PROD sin comprobar.
2. Resolver diferencia de consentimiento de agencias en Brevo vs CRM con evidencia por contacto y propósito, sin importar B2C históricos ni activar falsos. El propietario afirma consentimiento previo por formularios, pero el código actual NO lo transmite correctamente en todas las rutas. Retroactividad NO.
3. Desplegar en implementación paralela del plugin, preservar snapshot y test end-to-end con formularios reales, DOI, Supabase RPC y rollback físico; luego promoción gradual solo si verde. No aplicar directamente a WordPress PROD.
4. Certificar editorial DeepSeek y dos imágenes nuevas tras inspección de calidad UMS; HTML final, ALT, enlaces, baja, pruebas desktop/móvil.
5. Enviar únicamente correo de prueba a bandejas expresamente autorizadas; comprobar eventos, duplicados, DOI, bajas, 300/día; después iniciar B2B y B2C por separado. Ningún cliente se añade o recibe correo antes.
6. Documentar versión real, jobs/observabilidad, límites, copias, contratos y rollback.

## Estado
`CONSENT_BUG_FOUND=YES`
`CONSENT_PATCH_CANDIDATE=LAB_GREEN`
`BREVO_QUOTA_PLANNER=LAB_GREEN`
`BREVO_REAL_LIST_INVENTORY=PARTIAL`
`BREVO_LIVE_CONTACT_SYNC=OFF`
`NEWS001_CUSTOMER_SEND=OFF`
`WORDPRESS_PROD_CHANGES=NONE`
`ADDITIONAL_SUBSCRIPTIONS=NONE`.
