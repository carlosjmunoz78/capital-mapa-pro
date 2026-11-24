# CP89 · FACT-001 company scope gate · LAB

## HECHO
Se añade un gate ejecutable fail-closed sobre la rama CP88, sin tocar Worker, D1, secretos, cron, UMS, App/CRM, PROD ni main.

Fuentes vivas consumidas por el test:
- `cerebro-os/config/improvement_companies.lab.json`: Fenix Capital = `company_id=fenix`.
- `cerebro-os/registry/instances/SUP-001_FACT001-P5_CP88.lab.json`: instancia CP88 = `company_id=fenix-capital`, `registration_method=ADMIN_READONLY_EVIDENCE_SEED`.

## Resultado contractual
- `fenix` vs `fenix-capital` => `HOLD_COMPANY_ID_MISMATCH`.
- No se asume alias.
- No se atribuye la actividad P5 a la identidad canónica `fenix`.
- No se concede IAM.
- No se despacha UMS.
- Incluso con igualdad exacta de company_id, un registro administrativo CP88 no se convierte en aprovisionamiento FACT: `HOLD_NOT_FACTORY_PROVISIONED`.

## Rollback
Eliminar esta rama/PR. No existe cambio remoto de runtime que revertir.

## Next gate
1. Encontrar contrato firmado/verificable que autorice la correspondencia de identidad, si existe.
2. Encontrar emisor empresarial legítimo de `FACT.INVENTORY.READ` para JARVIS LAB, principal exclusivo, solo lectura y <=15 min.
3. Solo después ejecutar canario privado real JARVIS → FACT y correlacionar recibos.

Coste adicional contratado: 0 €. Estado: PARCIAL / FAIL-CLOSED CORRECTO.

## CP130 · Consolidación del generador y control plane FACT en LAB · 2026-11-24

Se portan exactamente los 12 archivos modificados de PR #277 (`639f245e30f19493906bfa68a552001588557f3d`) a la rama DRAFT de PR #290, cuya base previa de HEAD es `28e3e5de8ab732f9fef6484292fc01fcf2c34b18`. Base común `adda3e356094d91a87563c45584891207b2c3cc0`: 22 commits/12 archivos en #277 y 34 commits/70 archivos en #290, intersección de archivos 0. Se conserva #277 y sus evidencias originales hasta CI oficial y aceptación; no es un merge de genealogía ni promoción.

Prueba local combinada sobre blobs exactos: 14 tests de identidad/atomic scaffold, 25 tests CP82/88/89 y 12 tests Node de política de IDs y auditoría de cadena Cloudflare: 51 PASS, 0 FAIL. Generación temporal de 177 IDs, rechazo cross-company, concurrencia, commit atómico, transporte simulado, contrato de lectura privada y fail-closed. SHA256 log Python `526244c7c64b0c51a60a09d8ecca2f3b3787a22c368ce176482a4b422a8688bc`; Node `fca458f2f2ccb8a56fc0037921a27ba6b0d2b27bd1ae6ef828aca291a6fd6e55`. No se ejecuta transporte externo real ni se acredita CI oficial, despliegue, alta IAM o promoción. Notion Company Registry conserva FENIX_CAPITAL, LAB/PREPROD REGISTERED sin aislamiento validado; Alias Registry cubre motores/capacidades/skills, no autoriza equiparar tenants. No ampliar permisos.

Rollback: revertir este commit de port en #290 únicamente, con #277 y HEAD anterior intactos; no eliminar ramas ni tocar Cloudflare, Forge, main, App/CRM o PROD. Coste adicional nuevas suscripciones 0 EUR; coste marginal de CI por auditar. Siguiente gate: CI del HEAD exacto, comparar regresión de la pila completa, prueba física JARVIS -> FACT con autoridad legítima <=15 min y sin alias tácitos, canario Forge privado, tribunal y rollback.

## CP131 · Puerta IAM y cobertura CI consolidada · 2026-11-24

CP130 CI del SHA `86242db409087db6b5ab9bd4901942d244c74ba2`: run 45345235056 SUCCESS, jobs 138278092230 y 138278092499. CP131 añade las tres suites FACT ya existentes de tests/ al workflow oficial existente, sin crear otro. Se conserva verify_private_read_pair (OLD); el verificador nuevo exige un lector IAM independiente de confianza, emisor y principal exclusivos, compañía canónica exacta, mismo request/capability/version/entorno LAB y referencia de concesión en ambos recibos, estado activo no revocado y ventana <=900 segundos. No emite permisos ni cambia ningún caller desplegado. El lector IAM debe validar criptografía y revocación fuera de esta función; fixtures locales no acreditan ese adaptador real.

Evidencia física nueva (solo lectura): Cloudflare cuatro settings de JARVIS/FACT/recovery y cinco fuentes desplegadas revisadas sin exponer secretos. JARVIS y FACT Gateway OFF, sin service binding JARVIS→FACT, FACT.INVENTORY.READ no encontrado literalmente en las cinco fuentes inspeccionadas; NIA y UMS tienen contratos específicos que no son autoridad JARVIS. D1 P5 `fenix-capital`: 13 COMPLETED, 1 RECONCILE, último completed_at_ms=1795478447183. No se equipara con fenix. Browser 1 UI PROD accesible mediante Opera: TAKEOVER_PENDING; Supabase read-only confirma último heartbeat 2026-11-19T20:13:52.651Z, 1 lease PROD caducado, 10 HOLD, 0 QUEUED y 0 RETRY_WAIT. Desktop Commander offline. PR92 HEAD 1ef83b2a7cd5a6d40704311eefa3e86185e365e7 seis workflows SUCCESS, uno SKIPPED. No se arranca ni repara sesión PROD; wake-up físico sigue HOLD. Los dos workflows PREPROD antiguos hacen rearme recursivo y espera de hasta 45 min; no lanzar por riesgo de bucle/coste.

Prueba local de candidato CP131: 31 CP82/88/89/131 + 14 FACT + 12 Node = 57 PASS. SHA256 logs Python 08bcc0fc1e8645331b0ab1354cbc649e9ef1871f9b9e024322c1dde87748abe6, Node 5d60e0417a585369cfdecaee9d766063305eeccb369671c40693627d1b3ecfc0. Nuevas suites simulan IAM; NO prueba física de concesión. Rollback de código: revertir solo commit CP131 en PR290, conservar CP130. No nuevos workers, grants, crons, suscripciones, App/CRM/PROD ni Trading. Coste marginal no medido. Siguiente: adaptar una autoridad legítima existente exclusivamente LAB (o emitir nueva concesión de alcance mínimo mediante IAM autorizado), sin alias implícito, demostrar canario correlacionado; Browser LAB wake-up sin activar antiguos loops.
