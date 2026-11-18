# NEWS001 · Enrutamiento de altas por perfil · LAB · 18/11/2026

## Mandato propietario
Dos flujos separados, utilizando los diseños canónicos completos de CEREBRO: inmobiliarias (Brevo lista #18) y particulares (lista #17). Cada nuevo lead procedente de formularios web o de cualquier red social se evalúa por el perfil real y las evidencias de consentimiento; después de DOI confirmado, se planificaría la bienvenida y la inclusión en la edición semanal. **No** confundir envío de bienvenida tras alta con envío de newsletter semanal. Los particulares históricos no se importan. Excluir Salinas y contactos dados de baja, con rebote o duplicados.

## Código
- Gate existente `brevo_audience_gate.py` extendido para **inmobiliarias NUEVAS web/social**, además de las existentes en Brevo. Antes solo admitía inmobiliarias del histórico.
- `news001_onboarding_route.py`: decisión **pura/determinista, SIN IO**. Exige empresa correcta, perfil, fecha efectiva activation_at, evento con identificador, origen autenticado desde servidor, timestamp de consentimiento, finalidad newsletter, prueba identificable, DOI confirmado, baja/bloqueo revisado y no Salinas. Sin consentimiento NO hay alta comercial, aunque exista lead en CRM.
- Plan `plan_verified_subscribe`, `plan_doi_completed_welcome`, `plan_following_weekly_issue` — **ninguna operación ejecutada**. El resultado `PREPROD_DRY_RUN_ELIGIBLE` nunca se interpreta como autorización para enviar.
- No cambiar funciones actuales `fenix-web-lead` ni `social-lead-ingest` ni plugin WordPress `fenix-cerebro-leads`; están conectados con el CRM y requieren contrato OLD vs NEW, backup íntegro, replay, rollback y consentimientos reales.
- La fecha de activación real todavía no existe (`activation_at=null`). No falsificar.
- Los formularios actuales web ofrecen privacidad, no prueba de newsletter. El plugin vivo usa `!empty` y puede interpretar `"false"` como true. El ingest social inserta `consentimiento_comercial=false` sin importar la procedencia: debe corregirse en circuito separado de consentimiento real.
- Las dos listas Brevo #17 y #18 existen pero siguen con 0 contactos. No se ha escrito en Brevo ni enviado correo.
- Dos plantillas completas de diez módulos generadas por CEREBRO mediante GitHub Actions run #44280104275, NO la versión rosa/simplificada.
- No nuevas suscripciones ni Work. Tras cerrar newsletter, la siguiente prioridad SEO por tarea existente será D07 (competencia en Córdoba), salvo que la cola actual certifique otro gate.
