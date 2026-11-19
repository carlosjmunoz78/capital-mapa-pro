# KNOWLEDGE-FACTORY-001 · Extensión multi-departamento · 2026-11-19

## Estado físicamente verificado (Google Sheets, no inferido)

Hoja LAB existente: https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit

**NO MODIFICAR** App, CRM, producción, permisos, publicaciones ni la PR DRAFT.

- Apps Script universal e incremental instalado y sincronizado por Work: commit `f8fdd2e7749fd1312dbab895a9da140d886b0858`.
- Facebook: 42 agentes, 527 especialistas, 527 entregas internas únicas, 22 lotes Apps Script, hashes SHA-256 válidos y cola incremental sin duplicación.
- Instagram: 42 agentes, 527 especialistas, 527 asignaciones y 570 piezas candidatas, **importadas por Google Sheets API**, NO procesadas por Apps Script ni consumidas por agentes.
- LinkedIn: 42 agentes, 527 especialistas, 527 asignaciones y 570 piezas candidatas, **importadas por Google Sheets API**, NO procesadas por Apps Script ni consumidas por agentes.
- **Inventario total en Google**: 126 agentes, 1.581 especialistas, 1.581 asignaciones, 1.735 registros de biblioteca. Auditoría referencial determinista, 8.620 referencias resueltas, 0 errores de relación y 0 certificaciones.
- Únicamente Facebook tiene recibos internos (527). Gateway LAB verificado: 0 consultas. Uso real por agente: 0. Certificaciones: 0.
- Tabla `Departamentos` creada con Fénix Facebook, Instagram y LinkedIn. `Asignaciones` amplió cabecera K:L:M (`engine_id,environment,department_id`) para nuevas filas; las filas heredadas de Facebook conservan dichas celdas vacías y el código original tiene fallback.
- Se amplió la capacidad de filas de `Especialistas`, `Asignaciones` y `Biblioteca`; no se eliminaron registros ni se alteraron las 527 entregas de Facebook.

## Orígenes exactos e integridad

**Instagram**: `carlosjmunoz78/fenix-capital-cerebro-social`, rama `cerebro/instagram-enterprise-lab-v0-20261108`, artefactos `families/instagram/financial-real-estate/manifest.v1.json`, `roles.v1.json`, `knowledge-packs.v1.json`.
Motor de inventario: `SOC-001/SOCBOOT-001`, departamento `instagram`, empresa `fenix-capital`, entorno `LAB`, versión `1.0.0-candidate`.
El fuente dice `ROUTED_CANDIDATE_NOT_INGESTED_NOT_CERTIFIED`; por ello la biblioteca se etiqueta como **rutas candidatas, no conocimiento profesional certificado**. Las 527 referencias usan roles y overlays con un control de procedencia, sin trasplantar permisos de Facebook.

**LinkedIn**: mismo repositorio, rama `cerebro/linkedin-enterprise-lab-v0-20261113`, artefactos `linkedin_enterprise_v0/manifest.v1.json`, `roles.v1.json`. Motor `SOC-LI-FINANCIAL-REAL-ESTATE-V1`, departamento `linkedin`, empresa `fenix-capital`, entorno `LAB`, versión `0.1.0`. Sus roles provienen de un crosswalk lógico Instagram, no de certificación profesional ni plataforma. Etiquetados **DEFINED_NOT_TRAINED**, sin capacidades de publicación.

## Bloqueo externo — consumidor Gateway

Google Apps Script, durante la instalación, fue autorizado a modificar solo este Sheet y manejar triggers. **Eso no proporciona** al Gateway una identidad OAuth para consultar Sheets.

El Gateway necesita su propio consumidor autenticado, autorizado expresamente a leer **solo esta hoja**, con Google Sheets API `spreadsheets.readonly`, aislamiento por `company_id` y `department_id`, límites y auditoría. No publicar web app de Apps Script bajo permisos del propietario ni trasladar tokens a GitHub o Sheets.

Se requieren 3 lecturas autenticadas **desde un consumidor Gateway LAB** y una denegación de tenant ajeno antes de afirmar integración o uso real. Los tests actuales solo validan estructuras en la hoja y simulaciones.

## Continuación con coste 0 €

1. La importación mediante Google Sheets API **no dispara** `onEdit`. Para generar los recibos de Instagram y LinkedIn en el proyecto real es obligatorio invocar `cerebroLabQueueIncremental` desde una sesión autorizada dentro del proyecto o desde el menú Google Sheets **CEREBRO · LAB → Encolar cambios de conocimiento LAB**. No crear recibos manualmente.
2. Respetar límite de 600 entregas por día UTC y bloqueos/idempotencia; los 527 recibos Facebook del mismo día ya consumieron ese margen. Las ~1.054 entregas nuevas deben repartirse por días según cuota configurada.
3. No marcar `STAGED_NOT_INJECTED` como `TRAINED`; las 1.054 asignaciones candidatas requieren investigación sustantiva, fuentes primarias actualizadas, ensayos independientes y conexión real al Gateway.
4. Los inventarios SEO, productora e ingeniería necesitan identificación autoritativa de agentes antes de crear filas; no extrapolar tamaños de Facebook.
5. Mantener la PR #278 DRAFT. No tocar Cloudflare, GitHub Actions, PROD ni credenciales.

Rollback: quitar únicamente las filas nuevas de Instagram y LinkedIn tras snapshot/validación y eliminar el registro de esos departamentos; conservar todas las de Facebook. No se ha ejecutado rollback.
