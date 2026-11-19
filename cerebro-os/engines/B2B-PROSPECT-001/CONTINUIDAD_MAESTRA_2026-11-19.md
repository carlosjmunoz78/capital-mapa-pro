# CEREBRO OS · CONTINUIDAD MAESTRA · NEWS-001 + B2B-PROSPECT-001
Fecha: 19-11-2026 · Owner: Fénix Capital · Entorno nuevo motor: LAB · Coste adicional máximo: 0 €.
Este fichero prevalece sobre cualquier resumen anterior que interpretase el despliegue por provincias como «fases» que paran. **No hay fases con barrera de entrada ni pausa al pasar de territorio. Hay una sola cola continua y un orden inmutable.**
La rama `cerebro/b2b-prospect001-continuity-lab-20261119` es aislada: PROHIBIDO fusionar en main o desplegar en PROD por accidente.

## A. NEWS-001 · ESTADO EXISTENTE / HECHO (verificaciones reales del 18 y 19/11/2026)
- Plataforma: Brevo Free; remitente corporativo de NEWS-001 `hipotecas@fenixcapital.es`.
- Dos audiencias: #17 FENIX_NEWSLETTER_PARTICULARES (1 suscriptor), #18 FENIX_NEWSLETTER_INMOBILIARIAS (37 suscriptores tras incorporación).
- Campañas #121 FÉNIX PRO y #122 FÉNIX HOGAR: envío real 19/11/2026. Brevo devolvió cada una `sent=1, delivered=1, hardBounces=0, softBounces=0, unsubscriptions=0`. La entrega de una campaña a un usuario no valida aún el ciclo semanal.
- Automatizaciones de bienvenida Brevo #10 particulares y #11 inmobiliarias observadas ACTIVAS; vieja automatización #9 "NEW LETTER PARTICULARES" EN PAUSA, verificada en interfaz.
- Supabase proyecto `cluhljgonannaafpmblx`: Edge Function `cerebro-news001-weekly-v1` v5 ACTIVE; `cerebro-news001-leads-sync-v1` v1 ACTIVE; token de operación privado en Vault; ninguna clave en documentos.
- pg_cron #4 `news001-cerebro-weekly-v1`: ACTIVO `0 8 * * 2` (martes, 08:00 UTC). Primera ejecución autónoma real PENDIENTE, prevista martes 24/11/2026; confirmar ejecución de Edge, campañas, cuotas, ausencia de duplicados y entrega. Campañas semanales a las 10:30 y 10:50 UTC: 11:30/11:50 en horario CET; 12:30/12:50 en CEST. NO afirmar 11:30 local todo el año.
- pg_cron #3 `news001-cerebro-optin-bridge-v1`: ACTIVO `*/10 * * * *`. Historial SQL reciente: `succeeded`; validar HTTP real al revisar nuevos leads. No se acreditó aún un nuevo lead opt-in E2E.
- Runtime NEWS-001 actual limita a 140 contactos/lista y 280 total; si la lista crece por encima de esos máximos, hace HOLD y requiere ajustar una estrategia sin romper las cuotas compartidas. Brevo Free 300 emails/día en cuenta compartida, no 300 para B2B.
- NEWS-001 PR #276 DRAFT, `carlosjmunoz78/capital-mapa-pro`, rama `cerebro/news001-single-optin-lab-20261118`. NO fusionar ni tocar para este nuevo motor.
- Lista #18 fue ampliada de 1 a 37 contactos: 17 de lista #9 "Inmobiliarias · NEW LETTER" + 19 de lista #13 "Inmobiliarias casi colaboradores", 36 adiciones exitosas, sin fallos, sin mover originales. El propietario confirmó aceptación comercial para «casi colaboradores». Se conservaron supresiones: 6 bloqueados de #13 NO añadidos. Auditoría registrada en PR #276: https://github.com/carlosjmunoz78/capital-mapa-pro/pull/276#issuecomment-7017803917.
- Cruce CRM fenix_prod.inmobiliarias (SOLO LECTURA) y Brevo: 18 inmobiliarias activas reales, 16 coincidencias por email exacto dentro de #18 y ANDALUZA localizada por coincidencia nominal. Lucena Hogar Inmobiliaria e Inmobiliaria Virtual coinciden por correo y están en #18. "INMO HOGAR LUCENA" declarada por propietario como duplicado de Lucena Hogar: no crear ni modificar. Salinas: no hubo coincidencia textual en Brevo, pero si está bajo alias/dominio alternativo la exclusión no queda acreditada; mantener blacklist de exclusión permanente cuando se identifique.
- Nada de tocar App/CRM, web WordPress, SEO, DN S, ni los flujos originales. El nuevo B2B es INDEPENDIENTE de NEWS-001.

## B. B2B-PROSPECT-001 · ORDEN DEL PROPIETARIO (nueva captación de toda Andalucía)
Misión: identificar inmobiliarias ajenas a cartera actual, preparar relación comercial y conseguir que RESPONDAN PARA HABLAR o ENVÍEN UN EXPEDIENTE HIPOTECARIO. No Calendar, no enlace de reservas, no app de citas. Respuesta por el correo corporativo y teléfono visible en la web.

### ORDEN INMUTABLE DE LA ÚNICA COLA (15 prioridades)
1. TODOS los pueblos de **Córdoba** (sin Córdoba capital; no estaba en la secuencia solicitada).
2. TODOS los pueblos de **Jaén** (excluyendo capital).
3. **Jaén capital**.
4. TODOS los pueblos de **Sevilla** (excluyendo capital).
5. **Sevilla capital**.
6. TODOS los pueblos de **Málaga** (excluyendo capital).
7. **Málaga capital**.
8. TODOS los pueblos de **Granada** (excluyendo capital).
9. **Granada capital**.
10. TODOS los pueblos de **Cádiz** (excluyendo capital).
11. **Cádiz capital**.
12. TODOS los pueblos de **Almería** (excluyendo capital).
13. **Almería capital**.
14. TODOS los pueblos de **Huelva** (excluyendo capital).
15. **Huelva capital**.

**CRÍTICO: no implantar barreras «terminar fase 1 antes de descubrir fase 2».** El descubrimiento y el enriquecimiento pueden seguir en paralelo por toda Andalucía, pero el **orden de entrada a la cola de contacto** debe seguir EXACTAMENTE esas quince prioridades. Si se agota cuota diaria, conservar cursor/idempotencia y retomar el día siguiente desde el siguiente pendiente. Los contactos ya en seguimiento tienen acciones vencidas gestionadas bajo capacidad reservada; prohibido enviar duplicados por reintentos.

### TODOS los correos de una eventual secuencia deberán incluir:
- Dos llamadas a la acción claras y humanas: (1) «Respondednos con cuándo os viene bien hablar / llamadnos»; (2) «Si ya tenéis comprador, enviadnos un expediente o consultadnos su viabilidad».
- Dirección de respuesta: `hipotecas@fenixcapital.es` (confirmar gestión real de bandeja/respuestas; no personalizar con un remitente inexistente).
- Teléfono publicado en web Fénix Capital: **614 572 469**; el propietario lo identifica como teléfono de Belén. Fuente pública: https://fenixcapital.es/contacto/ y https://fenixcapital.es/inmobiliarias/.
- Links: https://fenixcapital.es/inmobiliarias/ ; https://fenixcapital.es/contacto/ ; CTA a página de envío/estudio de caso únicamente tras verificar URL y permisos reales. No crear enlaces inexistentes.
- Mensaje principal: Fénix Capital como apoyo hipotecario de su zona, proteger ventas y relación cliente-agencia, análisis ágil; colaboración económica **1.100 € por operación** según condiciones aprobadas y documentadas, sin fingir pagos por meras referencias ni concesión garantizada.
- Pueden existir varios emails de calentamiento con intervalos a decidir; **NO REDACTAR NI ACTIVAR** las campañas todavía. El propietario quiere DETENERSE al llegar al diseño/copy y revisar personalmente secuencia, tono, asuntos, oferta, condiciones, identidad, logos, links, teléfono, legal, pies y disparadores, porque de ello depende la expansión. Gate: `HUMAN_REQUIRED: HIGH_RISK` para aprobación comercial del copy y `LEGAL_REQUIRED` cuando proceda, no por cada trabajo mecánico.
- Hay que separar contactos nuevos/prospectos de colaboradores actuales. No enviarlos a NEWS-001 lista #18 y no disparar bienvenidas #10/#11.

### Stack gratuito y arquitectura
- CEREBRO (lógica determinista / jobs compartidos / FACT-001 scaffold; NO 150 servidores), GitHub para GitOps, Cloudflare Free si ya disponible, Brevo Free para mensajes a destinatarios habilitados, `hipotecas@fenixcapital.es` para respuestas, CRM como **fuente SOLO LECTURA** hasta que exista contrato y autorización de integración no invasiva.
- Datos empresa y contacto: `company_id`, `engine_id`, `environment`, `version`, `business_name`, `normalized_identity`, `municipality`, `province`, `is_capital`, `queue_priority`, `source_url`, `source_verified_at`, `email`, `contact_status`, `legal_contact_basis`, `consent_evidence`, `newsletter_exclusion`, `suppression`, `last_touch_at`, `next_touch_at`, `idempotency_key`, `reply_status`, `handoff_owner`.
- Orígenes a investigar sin escrapeo invasivo: censo oficial de municipios de Andalucía, webs corporativas y directorios con condiciones compatibles. Documentar cada URL, fecha y criterio de coincidencia. Empezar exploración por pueblos de Córdoba; el resto alimenta el mismo pipeline en orden.
- Regla de envío: **disabled=true** hasta que haya revisión comercial y elegibilidad normativa verificada; no se asume que un email público autoriza publicidad. El motor puede descubrir, deduplicar, enriquecer y preparar llamadas/revisión sin enviar emails no solicitados. Respetar oposición y listas de baja. El día de apertura, fijar reserva de capacidad para las newsletters y bienvenidas existentes, cuota real Brevo y follow-ups. `send_cap <= min(300, cuota_dia_verificada, saldo_restante)`; STOP al error, retry idempotente.
- Anti duplicación: dominio + entidad + nombre normalizado + email + coincidencias CRM/Brevo; no reenviar al mismo destinatario la secuencia al reimportar. Excluir Salinas por nombre/alias/dominio una vez verificado; mantener supresiones y duplicado INMO HOGAR LUCENA.
- Respuestas: cuando entre respuesta comercial o interés / expediente / BAJA, parar secuencia y derivar a humano Belén o equipo comercial; nada de pedir envío por email de documentación personal sensible sin un canal seguro ya habilitado.
- Métricas: municipios cubiertos, empresas únicas verificadas, contactables con base legal, capacidad diaria usada, correos efectivamente entregados, rebotes, quejas, bajas, respuestas, expedientes, reuniones aceptadas, acuerdos y firmas. Comparar conversiones por provincia/municipio, no métricas vanidosas.
- Zero extra subscriptions. Preservar App/CRM/Supabase/WordPress/SEO/Notion/NEWS-001. Backup/snapshot+contratos+tests+comparación OLD/NEW+rollback+PREPROD de nuevo motor solo cuando aplique; en esta etapa LAB aislado, sin tocar el PREPROD de App (no existe).

## C. ESTADOS CLAROS / NO REPETIR
HECHO: NEWS001 envíos piloto entregados, #9 pausada, #10/#11 activas (verificación precedente), #3 y #4 cron activos, #18 37 suscriptores, fuente web/teléfono confirmados, nueva rama LAB creada.
EXISTENTE: GitHub factory, Brevo account, dominio y correo, páginas web, CRM real (intocable para este trabajo).
PARCIAL: una prueba real semanal el martes 24/11 pendiente; newsletter onboarding de nuevos leads sin prueba E2E verificada; exclusión Salinas por alias/dominio pendiente.
DEFINIDO: motor B2B-PROSPECT-001 cola única priorizada Andalucía, mensajes de doble CTA, límites y aprobaciones.
POR AUDITAR/CONSTRUIR: inventario oficial de todos municipios; extracción respetuosa de inmobiliarias; calidad de datos; capacidad de respuestas en correo; conexión CRM no invasiva; seguimiento y comercialización.
BLOQUEADO EXPRESAMENTE: escribir versión definitiva de los emails, publicarlos, activarlos o enviar campaña nueva a prospectos hasta revisión comercial y verificación legal.

## D. PRIMEROS PASOS AL RETOMAR (sin volver a estudiar lo hecho)
1. Leer este archivo y `NEXT_CHAT_PROMPT.md`; no repetir NEWS-001 ni reestructurar arquitectura. Mantener orden continuo.
2. Continuar scaffold LAB con FACT-001; ejecutar tests del planificador offline (no emails).
3. Obtener inventario oficial íntegro de municipios andaluces; ordenar primero todos los pueblos de Córdoba; registrar fuentes y QA. Descubrir inmobiliarias, sin enviar publicidad.
4. Dedupe contra CRM/Brevo mediante lectura; protección de datos y exclusiones; crear propuesta de cola persistente en infraestructura existente, sin tocar transaccional PROD.
5. Detenerse al alcanzar la **redacción de los emails** y presentar al propietario la revisión editorial de máxima calidad (doble CTA, 1.100 €, enlaces, 614 572 469).
6. No declarar PROD, captación completa, envíos habilitados ni primer ciclo semanal NEWS001 hasta evidencia física.
