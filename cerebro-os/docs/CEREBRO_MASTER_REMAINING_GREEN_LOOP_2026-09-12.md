# CEREBRO OS · MASTER REMAINING GREEN LOOP · 2026-09-12

Estado de partida y progreso verificado:
- 177/177 motores = LAB_GREEN.
- Make PROD = 25/25 inventariado/clasificado.
- Make CORE = 62/62 inventariado/clasificado; 8/8 active edges tienen política preserve/wrap con CI GREEN; 54 inactive disponen de política determinista de migración/quarantine por clase, sin autoactivación ni borrado.
- Make TEST = 120/120 inventariado/clasificado de forma exhaustiva: 2 active + 1 error histórico + 117 inactive.
- Support folders AUDITORÍA/LEGACY + PREVENTIVO/RECUPERACIÓN + ALERTAS/MONITORIZACIÓN = 19/19 inventariados.
- Social PROD: Facebook/Instagram/LinkedIn/YouTube contratos principales auditados; TikTok aparcado hasta existir cuenta oficial.
- ADS CORE: caller parity + contrato vivo + CI GREEN.
- CEREBRO Console V0: ruta CONSOLE → GATEWAY → POLICY → ENGINE → AUDIT protegida por test de scope; nunca directo a modelo.
- MCP/Computer Use: policy y orden de fallback definidos; no puede saltarse kill-switch, auditoría, scope, credenciales ni límites económicos.
- Recovery gate: existe runtime evidence-first que separa source backup/rebuild/rollback rehearsal de provider restore y nunca permite restore destructivo automáticamente.
- Observability/cost gate: existe runtime fail-closed con logs, métricas, incidentes, coste medido y MONEY_LIMIT.
- Dependency preservation gate: existe runtime para App/CRM/Supabase/Notion/WordPress/SEO; exige inventario, mapa, contrato actual, tests, implementación paralela y rollback; nunca autoriza borrar OLD.
- Promotion gate final: existe runtime canónico con contracts, permissions, tests, evaluation, tribunal, observability, rollback, backup, rebuild, cost, policy y environment evidence; PROD_GREEN nunca se concede automáticamente.

Este documento NO declara PROD global. Es la cola canónica de cierre técnico posterior a LAB_GREEN.

## Orden de trabajo y estado

1. PROD folder 25/25: **HECHO / GREEN inventory-classification**.
2. SEO PROD activo: **HECHO / PRESERVE ACTIVE EDGE / GREEN_CODE_CI**.
3. YouTube auxiliares PROD: **HECHO / GREEN_CODE_CI**.
4. One-shots PROD Facebook/Instagram: **HECHO / QUARANTINED HISTORICAL**.
5. WordPress anomaly en carpeta PROD: **HECHO / CLASSIFIED / PRESERVED**.
6. Facebook PROD: **HECHO contract/parity code / PROD execution gated**.
7. Instagram PROD: **HECHO contract/parity code / PROD execution gated**.
8. LinkedIn PROD: **HECHO contract/parity code / PROD execution gated**.
9. YouTube PROD: **HECHO contract/parity code / PROD execution gated**.
10. TikTok: **PARKED_ACCOUNT_NOT_AVAILABLE**. No bloquea resto.
11. CORE 62/62: **PARCIAL AVANZADO** — inventory 62/62 GREEN, active-edge parity 8/8 GREEN_CODE_CI, inactive migration policy 54/54 defined fail-closed; falta convertir las clases migrables en runtime/replay específico donde aún no exista.
12. TEST 120/120: **HECHO / GREEN inventory-classification**.
13. AUDITORÍA/LEGACY 9: **HECHO inventory / preserved evidence; caller retirement sigue bajo cutover gates**.
14. PREVENTIVO/RECUPERACIÓN 2: **PARCIAL CONTROLADO** — inventory/contracts + recovery gate GREEN_CODE_CI; rollback rehearsal real y provider restore siguen sin evidencia suficiente.
15. ALERTAS/MONITORIZACIÓN 8: **HECHO inventory/contracts; active execution no se fabrica**.
16. Credenciales/identidades: **HECHO registry + broker + vault refs + reuse/no-reask + secret guards; runtime proofs externos según edge**.
17. MCP/connectors/scripts/computer-use: **HECHO policy/registry/fallback/kill-switch contract; ejecución GUI real pendiente de disponer del runtime MCP correspondiente**.
18. CEREBRO Gateway/Console: **GREEN_CODE_CI V0 contracts/path; UI/runtime desplegado no reclamado**.
19. Multiempresa: **GREEN_CODE_CI en contratos/scope; integraciones externas se validan una a una**.
20. Backup/restore/rebuild/rollback: **GREEN_CODE_CI del gate / EXTERNAL_PROOF_PENDING** — source recovery y provider restore son dimensiones separadas; PROD restore no se declara probado.
21. Observabilidad/costes: **GREEN_CODE_CI del gate / EVIDENCE_PER_ENGINE_PENDING** — logs + métricas + incidentes + coste medido son obligatorios; 0 € adicional default y MONEY_LIMIT fail-closed.
22. Security/policy/human-exception: **GREEN_CODE_CI estructural; PROD depende de evidencia real y solo ocho razones canónicas**.
23. App/CRM/Supabase/Notion/WordPress/SEO dependency map + OLD/NEW wrappers: **GREEN_CODE_CI del gate / EVIDENCE_PER_ENGINE_PENDING** — no se permite borrar OLD y se mantiene CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR.
24. External integrations: **PARCIAL / promover una por una con permisos reales**.
25. Promotion gate final: **GREEN_CODE_CI DEL GATE / BLOQUEADO POR EVIDENCIA EXTERNA DONDE FALTE**.
26. PROD_CANDIDATE por motor/familia: **CALCULABLE POR GATE / NO declarar sin todas las evidencias reales**.
27. PROD gradual: **NO ejecutar automáticamente**; publicación, gasto, firma o mutación sensible requieren gate humano canónico.

## Estados permitidos

HECHO / EXISTENTE / PARCIAL / DEFINIDO / PLANIFICADO / POR_AUDITAR / PARKED_EXTERNAL_DEPENDENCY / GREEN_CODE_CI / PROD_CANDIDATE / PROD_GREEN.

## Regla

CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR.
