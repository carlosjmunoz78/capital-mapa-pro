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


## Entrada común para creadores LAB

FACT-001 acepta ahora `scaffold(..., agent_inventory=[{"agent_id": "..."}, {"agent_id": "...", "subagent_id": "..."}])` o el parámetro de CLI `--agents-json`. Se valida todo el inventario antes de crear archivos. El inventor aporta identidades verificables por su fuente y el hook elimina duplicados por pareja agente/subagente. Las altas posteriores reutilizan `register_agent_candidate`. Cada candidato deja una solicitud duradera sin despacho, formación ni permisos.

Los creadores externos de App, Skill Factory, Ingeniería, Social, SEO y UMS-001 deben llamar esta entrada desde su LAB cuando dispongan de un inventario emitido por su creador real. El catálogo de perfiles, skills, capacidades y motores históricos se conserva como evidencia de cobertura, sin convertirlo en identidades. La entrega a Google sigue bajo la verificación de fuente e IAM existente. Estos cambios viven en la PR DRAFT.
