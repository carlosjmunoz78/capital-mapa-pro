# NEWS-001 / Brevo Free / cohort selection / 17 noviembre 2026

## Nueva decisión del propietario
1. **B2B INMOBILIARIAS**: de los contactos históricos ya presentes en Brevo, interesan únicamente los de agencias inmobiliarias. No se eliminan los demás ni se transfiere/recupera el histórico B2C. La condición de estar en Brevo por sí sola no acredita marketing consent; filtrar por consentimiento demostrable y por no baja/supresión antes de una campaña.
2. **B2C PARTICULARES**: solo nuevos leads recibidos por los formularios propios de `Fénix CEREBRO Leads` **desde el instante de activación real del pipeline**; sin importación de contactos B2C históricos de Brevo. Filtro de consentimiento expreso de newsletter, prueba del consentimiento, confirmación DOI para los nuevos, deduplicación y respeto de baja.
3. Dos listas/segmentos separados, bienvenida B2C diseñada de 5 mensajes y bienvenida B2B por certificar, newsletters semanales; usar Brevo Free (hasta 300 emails/día según oferta publicada, comprobar cuota real antes de programar). Prioridad de reparto: confirmaciones/welcome válidas > campañas en lotes; idempotencia, reintentos sin duplicar y no consumir cupo en leads no elegibles.
4. La web/WordPress y CRM siguen canónicos para lead/consentimiento; Brevo solo transporte. NO usar Make, Hostinger Reach, suscripciones nuevas, ni alterar App/CRM/WordPress PROD hasta cierre de gates.

## Auditoría actual de lectura
- Brevo UI muestra 87 contactos globales, mezcla de contactos reales y QA. No equivale a 87 suscriptores elegibles, ni a número de agencias.
- Notificaciones de la cuenta: listas `[24] FENIX PREPROD · Inmobiliarias` y `[23] FENIX PREPROD · Hipoteca particulares` registradas el 1 oct; **no certificadas como listas comerciales finales PROD**. Evitar mezclar PREPROD y PROD.
- WordPress PROD `fenix-cerebro-leads` 1.3.6-preprod: valor `consent_marketing:false` hardcoded en rutas de captura y parsing PHP `!empty($data['consent_marketing'])`. El string literal `"false"` en PHP puede activar una condición verdadera: bloquear sincronización hasta corregir y probar el sistema de consentimiento. **No afirmar que los 87 dieron permiso ni que los clientes no lo dieron.**
- NEWS-001 y editor visual aún en LAB con envío OFF; fotos B2C/B2B de demo rechazadas visualmente.

## Contrato ejecutable LAB
`cerebro-os/engines/CEREBRO-NEWS-001/brevo_audience_gate.py`: selecciona únicamente `brevo_existing + inmobiliaria + marketing consent verified + evidencia + no suppression` para B2B y `fenix_cerebro_leads + particular + received_after_activation_at + consentimiento + DOI` para B2C. Los tipos booleanos deben ser booleanos estrictos (nunca string `"false"` ni string `"true"`). Toda decisión se limita a `ELIGIBLE_FOR_PREPROD_TEST_ONLY` o `HOLD`, con `send_authorized=false` y `contact_mutation_authorized=false` por defecto. No lee ni modifica contactos y no realiza llamadas a Brevo. Tests en GitHub Actions de casos positivos/negativos; no es integración PROD ni auditoría de consentimiento por cada contacto.

## Gates de promoción
1. QA de PDF/HTML/texto original/UMS-001, DOI y baja; profesional QA en dos audiencias.
2. Inventario exacto de listas/agencias y prueba documental de consentimiento + estado de supresión; no enviar a personas no elegibles.
3. Reparar consentimiento de WordPress con backup, pruebas de cadena `"false"` y comparativa/rollback real antes de tocar sitio.
4. Fijar en config versionada `activation_at` **solo cuando arranque realmente la captación nueva**, evitar fechas arbitrarias del momento de escritura.
5. Tests de envío solo a buzones internos autorizados y monitor de límites Free; avanzar B2B/B2C separadamente, sin dependencias cruzadas.

Estado: `AUDIENCE_POLICY_DEFINED`, `GUARD_LAB_CODE`, `BREVO_CONTACT_AUDIT_PARTIAL`, `SEND_OFF`, `PROD_HOLD`.
