# NEWS001 CEREBRO weekly runtime · V1
Independiente de ChatGPT. Dos ediciones nuevas por semana, listas #17 y #18, 10 bloques, 2 imágenes y logo oficial. Fuentes: titular español verificado del RSS oficial del Banco de España; si no hay, edición guía práctica rotativa sin cifras inventadas. Nada de DeepSeek o IA de pago.

Acciones: preview (sin Brevo), draft (crea borradores de prueba), owner-test (solo carlosj.munozcabeza@gmail.com), pilot-release (primera programación tras prueba), weekly (ejecución automática martes 07-10 UTC). Valida máximo 140 contactos/lista y 280/día, compara nombres semanales para impedir duplicados. No toca plantillas y automations de bienvenida; no activa campañas anteriores.

Operador usando token privado Vault y BREVO_API_KEY ya configurada; cron semanal previsto a las 08:00 UTC de los martes. Ajuste de horario CET/CEST: campañas 10:30 y 10:50 UTC, equivalentes a 11:30/11:50 en invierno o 12:30/12:50 verano. Rollback: cron.unschedule('news001-cerebro-weekly-v1').
