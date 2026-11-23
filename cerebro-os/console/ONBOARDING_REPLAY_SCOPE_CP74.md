# Onboarding · CP74 · Ámbito de reintentos de órdenes (LAB)

## Defecto OLD

El motor `OnboardingQueueEngine.execute` devolvía `ALREADY_QUEUED` cuando `request_id` y `company_id` coincidían, sin comprobar `version`, `environment`, `user_id` y contexto. La referencia `company:otraempresa` se aceptaba como texto y se almacenaba en el nuevo job.

## Contrato NEW

- Los trabajos nuevos incorporan `environment` en el payload para proteger el replay cruzado entre LAB y PREPROD.
- Los reintentos deben coincidir exactamente en empresa, versión, identidad autenticada y contexto. Los payloads de LAB heredados, que no tienen campo de entorno, se admiten exclusivamente si el resto coincide.
- Rechaza explícitamente referencias de contexto con prefijo `company:` que no correspondan al `company_id` seleccionado. Otros contextos se conservan por compatibilidad con el loader existente.
- La respuesta de éxito `ALREADY_QUEUED` se mantiene para reintentos verdaderamente idénticos y no se crea otro job.
- Sin cambios del esquema SQLite, credenciales, permisos, cron ni infraestructura. No se habilita Gateway.

## Pruebas y límites

- 14 pruebas: OLD 6 fallos y 1 error reproducidos; NEW 14/14 PASS, incluidas 4 pruebas originales de la consola.
- Rollback Git local exacto; commit únicamente en rama LAB paralela.
- No elimina la necesidad de una identidad establecida por IAM ni sustituye al contrato de recibos firmados. Comandos de usuario desde un frontend sin broker autenticado permanecen fuera del alcance. Coste incremental 0 €.