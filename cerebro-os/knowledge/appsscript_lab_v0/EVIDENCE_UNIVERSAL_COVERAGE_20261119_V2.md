# CEREBRO · KNOWLEDGE-FACTORY-001 · Cobertura multiempresa LAB · V2 (2026-11-19)

## Verificación de registros

Google Sheet: https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit

| Departamento | Agentes/roles | Subagentes/plantillas | Biblioteca | Recibos físicos Apps Script |
| --- | ---: | ---: | ---: | ---: |
| Facebook (fenix-capital) | 42 | 527 | 595 | 527 |
| Instagram (fenix-capital) | 42 | 527 | 570 | 0 |
| LinkedIn (fenix-capital) | 42 | 527 | 570 | 0 |
| SEO (fenix) | 50 plantillas | 141 plantillas | 192 referencias/plantillas | 0 |
| TOTAL | 176 | 1722 | 1927 | 527 |

Las 1.722 asignaciones de referencia y **9.043 referencias verificadas** pasaron control determinista de correspondencia entre empresa, motor, entorno, rol, subagente, reglas, versión y fuentes (cero errores). 0 agentes con acceso Gateway E2E, 0 certificados. 1.195 candidatos sin recibos de Apps Script. **No confundir registros, templates, conocimientos candidatos ni hashes con agentes formados.**

Tablas nuevas: `Departamentos`, `Cobertura_Universal`, `Perfiles_Transversales`, `Dashboard_Global`; 179 motores documentales históricos (177 + HCI-001/MOTION-001) más UMS-001 y CEREBRO-NEWS-001 = 181 entradas catalogadas, sin afirmar que estén activas.

## Fuentes

- Facebook: `fenix-capital-cerebro-social`, rama `cerebro/facebook-manual-knowledge-remediation-v1-20261118`, PR #13.
- Instagram: mismo repo, rama `cerebro/instagram-enterprise-lab-v0-20261108`, `families/instagram/financial-real-estate/{roles.v1.json,knowledge-packs.v1.json}`; fuentes aún candidatas.
- LinkedIn: mismo repo, rama `cerebro/linkedin-enterprise-lab-v0-20261113`, `linkedin_enterprise_v0/roles.v1.json`; `DEFINED_NOT_TRAINED`.
- SEO: `fenix-capital-inmo-map`, rama `cerebro/operativa-agent-directory-prod-candidate-20261117`, `cerebro/registry/seo001-role-templates-191.sourced.v1.json`; `SOURCE_ROSTER_ROLE_TEMPLATES_ONLY`. **Preservado `company_id=fenix` como identidad separada**, sin equiparar automáticamente a `fenix-capital`. Ningún permiso entre empresas.
- Registro histórico ampliado de 179 motores: `fenix-capital-inmo-map/cerebro/registry/engine-registry.v1.json`.
- Ingeniería: `cerebro/registry/role-agent-registry.v1.json`, 10 perfiles + 1 comercial, no actores LAB habilitados.
- Productora: `cerebro/knowledge/creative-media-knowledge-registry-v1.json`, 12 consumidores potenciales, no agentes.
- Fábrica de skills: `cerebro/registry/skill-operational-wrapper-registry-v1.json`, 5 wrappers, no agentes; `cerebro/skills` y sus ramas históricas intactos.

## Alta de futuros motores/agentes

Hook **aditivo en rama DRAFT**, commit `9d1492e9ec136d484aee437dfa009ffea870c4e3`: `cerebro-os/factory/knowledge_factory_hook.py` se invoca desde `cerebro-os/factory/factory.py` para motores NUEVOS creados con esa versión Python. Genera contratos LAB pendientes, no llama APIs, no crea workers, no certifica, no requiere pago y no escribe en PROD. `register_agent_candidate` es una API local **que deben integrar los creadores de agentes**; actualmente no se autoejecuta en otras fábricas.

Importante: la App contiene también las fábricas JavaScript `cerebro/factory.mjs` y `factory-v1.mjs` y la fábrica de skills. Sus integraciones deben estudiarse como extensión paralela sin alterar el número/contratos de scaffold existentes; **aún no se han instrumentado**. Tres unit tests locales del hook Python pasaron; ninguna prueba de despliegue a PROD.

## Bloqueos

1. Escritos de Google Sheets API **no disparan onEdit**: los lotes IG/LI/SEO necesitan encolado dentro del proyecto Google Apps Script autorizado. Límite vigente configurado 600 recibos por día UTC, reanudable.
2. Gateway LAB aún sin identidad consumidora OAuth `spreadsheets.readonly`, política y tres lecturas reales + una denegación cross-company. NO habilitar endpoint público ni reutilizar credenciales de propietario.
3. Cada especialidad requiere fuentes primarias vigentes, ejercicios profesionales y evaluación independiente antes de formar/certificar.
4. Trading aislado. No GitHub Actions, no Cloudflare, no ordenador local. Coste adicional de infraestructura 0 €.

Rollback: commits GitHub reversibles, hoja con restauración selectiva tras snapshot. App/CRM/PROD no modificados; rollback físico no ensayado. PR #278 permanece DRAFT sin merge.
