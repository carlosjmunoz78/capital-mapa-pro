# FACT-001 · Knowledge Factory universal enrollment · LAB V0

- Al ejecutar `factory.scaffold` para un **motor nuevo**, el mismo scaffold escribe un contrato de conocimiento sin hacer llamadas externas. Esto afecta únicamente motores creados con esta revisión en la rama DRAFT, no motores históricos ni PROD.
- Artefactos nuevos: `training/knowledge_factory_enrollment.json`, `events/KNOWLEDGE_ENROLLMENT_REQUESTED.contract.json`, `jobs/knowledge_enrollment.pending.json`.
- Para un **agente o subagente** creado posteriormente, su creador debe llamar `register_agent_candidate(engine_path, agent_id, subagent_id)` del módulo `knowledge_factory_hook.py`. Esta integración existe como API local; los creadores externos no quedan instrumentados hasta adaptar sus puntos de alta.
- Estado inicial: `PENDING_FACTORY_IAM`, `NOT_INGESTED`, `NOT_CERTIFIED`. Ningún permiso, invocación de IA, coste, token, cron, publicación o integración privada es activado.
- Firma/identidad: el `company_id` recibido por `scaffold` es **una alegación no verificada**. Nunca debe autorizar lectura multiempresa. El Gateway necesita una identidad firmada y una credencial OAuth con `spreadsheets.readonly` para el consumidor LAB.
- El lote de Google Sheets gestionado mediante API debe encolarse explícitamente dentro de Apps Script, ya que las escrituras API no disparan onEdit. La fábrica NO está conectada todavía a un consumidor Gateway real.
- Prueba offline realizada antes de la entrega: tres tests de aislamiento, idempotencia y rechazo de rutas inseguras; tras la integración de FACT-001 no se ha ejecutado una prueba completa del scaffold real en CI (GitHub Actions bloqueado).
- Rollback: revertir el commit de esta PR DRAFT. No se han alterado ramas protegidas ni producido credenciales.

**Diferencia esencial:** auto-creación de la petición de conocimientos por motor = **HECHO EN CÓDIGO**, auto-incorporación en Google / entrenamiento de cada agente = **PENDIENTE DE IAM Y ENLACE DEL CREADOR**.
