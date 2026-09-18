# CEREBRO OS · cierre maestro y bloqueos finales · 2026-09-18

Estado: PARCIAL / HUMAN_REQUIRED en gates finales. Todo el trabajo seguro y autónomo posible desde este canal queda ejecutado y documentado; no se declara PROD autónomo global.

HEAD canónico de partida: `cb97aad0dec9a31b3953978e900cd3e385ae84e4`.

## HECHO

### Security · Supabase PROD
- Incidente anon SECURITY DEFINER: cerrado; anon execute = 0 en la categoría corregida.
- Mutable search_path: dos warnings cerrados.
- `pg_net`: disposición segura `PRESERVE_AND_AUDIT`; no se mueve sin rebuild/rollback.
- Inventario ACTIVE de Edge Functions para `fenix_prod_session_context()`: 42 superficies inspeccionadas.
- 13 callers directos descubiertos durante el loop.
- 13 de 13 migrados al patrón `Bearer -> auth.getUser() -> service_role -> fenix_prod_actor_context_by_auth_server`.
- Callers directos ACTIVE conocidos pendientes de `fenix_prod_session_context()`: `0`.
- `authenticated EXECUTE` del RPC legacy todavía NO se revoca: falta E2E HTTP autenticado y evidencia suficiente de ausencia de callers REST/RPC externos fuera del inventario Edge.

Evidencia principal:
- `cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md`
- `cerebro-os/evidence/security/SUPABASE_PROD_SESSION_CONTEXT_FINAL_CALLER_CLOSURE_20260918.md`

### Cierre final del caller legacy
- `fenix-document-existing-backfill` desplegado en PROD v8, ACTIVE, Verify JWT ON.
- SHA vivo: `cfe78207a52d5edaab2a02c1938394d55cd8e28aeef0c1acea2edcfc907de810`.
- llamada directa a `fenix_prod_session_context()` ausente.
- `auth.getUser()` y `fenix_prod_actor_context_by_auth_server` presentes.
- ACL pre-retiro capturado: authenticated=true, anon=false, service_role=true, definition MD5 `42fc119c18a2c7d8e500bd9bee1bb90c`.

### PREPROD / Engine Factory
Post-merge del cierre de callers:
- Engine Factory #1092: SUCCESS.
- FORGE PREPROD #39: SUCCESS.
- deploy privado: SUCCESS.
- contrato de aislamiento: SUCCESS.
- observabilidad persistente PREPROD: SUCCESS.
- artifact: `10569043087`.
- artifact digest: `sha256:d4d5d9d1c232f7998671979962b9e6e55d184e9ae689782dbeccfa079d623609`.
- artifact expired: false.

### Advisory
Professional Advisory PREPROD permanece GREEN como capacidad aislada PREPROD/advisory; esto no equivale a autonomía PROD global.

## PARCIAL / BLOQUEOS FINALES

### SECURITY
1. El último caller Edge conocido ya está migrado; quedan `0` callers directos conocidos entre las 42 Edge Functions ACTIVE inspeccionadas.
2. Falta E2E HTTP autenticado con un token real reutilizable antes del retiro del ACL legacy.
3. Falta cerrar suficientemente la ausencia de callers REST/RPC externos fuera del inventario Edge.
4. Leaked-password protection sigue pendiente de un canal soportado de escritura de Auth config.
5. El incidente separado de secreto Cloudflare sigue requiriendo inventario de consumidores + rotación + verificación post-rotación.
6. `pg_net` queda preservado hasta prueba de rebuild/rollback.

### RECOVERY
- El restore real de proveedor sigue bloqueado por `MONEY_LIMIT`: no se ha autorizado un recurso Supabase adicional de pago ni existe objetivo aislado gratuito demostrado.
- Rollback de fuente y rehearsals locales/CI: verdes.

### OBSERVABILITY
- PREPROD persistente: verde.
- PROD global por motor: aún falta mirroring/wiring y evidencia de logs/métricas/incidentes por motor sin romper tablas legacy.

### FINOPS
- El pago GCP fue reportado por el usuario como resuelto.
- Sigue faltando evidencia autoritativa del total mensual exacto de GCP y atribución real por familia/engine.
- No se inventa importe ni se declara 0 € sin evidencia.

### PROMOTION
- Global PROD/autonomy permanece `false`.
- La promoción automática sigue bloqueada hasta cerrar SECURITY, RECOVERY, OBSERVABILITY y FINOPS y existir autorización explícita.

## HUMAN_REQUIRED exacto

Para seguir desde aquí solo existen gates humanos/reales:

- `HIGH_RISK`: redeploy/retirement final de `fenix-document-existing-backfill` y posterior ACL retire cuando exista E2E.
- `SECURITY_INCIDENT`: rotación del secreto Cloudflare tras inventario de consumidores.
- `MONEY_LIMIT`: restore real aislado de proveedor si requiere coste.
- `LOW_CONFIDENCE` / credencial operacional: E2E HTTP autenticado si no se dispone de bearer de prueba soportado.

## Regla de cierre

No considerar CEREBRO OS globalmente terminado/autónomo en PROD hasta que los gates anteriores tengan evidencia física. El trabajo ordinario seguro puede seguir en PREPROD y en los motores ya validados sin levantar estos bloqueos.
