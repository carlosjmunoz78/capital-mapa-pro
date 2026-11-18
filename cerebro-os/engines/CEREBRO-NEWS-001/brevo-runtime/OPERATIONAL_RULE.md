# NEWS001 · Orden operativa registrada · 18-11-2026
**Decisión del propietario:** los nuevos leads que hayan aceptado comunicaciones comerciales pueden incorporarse a la newsletter correspondiente sin doble opt-in ni nueva autorización individual del propietario. Dar la bienvenida inmediatamente mediante las automatizaciones ya activas #10 (particulares) y #11 (inmobiliarias).

**Límite obligatorio y automático:** ser lead **no demuestra por sí solo** consentimiento para newsletters. El artículo 21 de LSSI exige consentimiento previo o relación contractual previa en productos similares. Esta configuración utiliza el campo ya existente `consentimiento_comercial = true` y `source_payload.consent_marketing = true`; excluye bajas, bloqueos, contactos sintéticos, otras audiencias y fuentes no fiables. No agregar al CRM sin permiso ni alterar la lógica existente.

**Operativa:** Cron ligero en Supabase es solamente transportador; el motor editorial seguirá externo; coste adicional 0€. El sincronizador crea/añade únicamente a listas #17 y #18, jamás dispara envíos de campañas masivas. El cron evita reactivar bajas comprobando Brevo antes de escribir. Contrato: company_id=fenix, engine_id=CEREBRO-NEWS-001, environment=PROD-controlled, version=v1.
**Roll back:** `select cron.unschedule('news001-cerebro-optin-bridge-v1');` deja intacto WordPress, CRM y Brevo.
