# Facebook caller map — evidencia live Make — 2026-09-12

## Alcance

Evidencia de dependencias lógicas del bloque Facebook dentro de `30 · FENIX · CORE E INTELIGENCIA` (folder 520864). No implica borrado de OLD ni promoción a PROD.

## Estado live observado

La búsqueda live de escenarios CORE con `Facebook` devuelve los escenarios de preflight/router/analítica/control relevantes. Los tres legacy supersedidos permanecen `inactive`, con `incompleteExecutions=0`:

- 9530582 · Preflight directo Texto + enlace V1
- 9528450 · Preflight publicaciones texto V1
- 9532848 · Preflight directo Vídeo corto V1

El router universal directo vigente en esta familia, `9533499 · Facebook · Router universal directo de formatos · V3`, está también inactivo y no publica. Su blueprint contiene rutas Data Store, no módulos de publicación Facebook.

## Destinos inspeccionados en 9533499

- Texto orgánico simple → `9530484` (V2 directo sin rollups)
- Texto + enlace → `9531078` (V2 completo)
- Imagen → `9531133` (V2 imagen)
- Vídeo corto → `9533424` (V2 vídeo corto)
- Vídeo largo → bloqueado (`BLOCKED_FORMAT_NOT_ENABLED`)

Los IDs legacy `9530582`, `9528450`, `9532848` no aparecen como destino de las rutas inspeccionadas del V3.

## Conclusión

**HECHO / GREEN_MAKE_CORE_CALLER_MAP:** dentro de la familia Facebook CORE inspeccionada, el router V3 apunta a los reemplazos V2 y no a los tres legacy supersedidos. Los legacy continúan preservados e inactivos.

**PARCIAL / NO PROD CLAIM:** esto no demuestra todavía ausencia absoluta de referencias fuera de la familia CORE ni que el runtime CEREBRO esté live en el entorno objetivo. Por tanto no autoriza borrado físico.

## Gate de retirada

La retirada física sigue bloqueada hasta que se cumplan simultáneamente:

- caller map completo para el alcance objetivo;
- replay OLD vs NEW verde;
- rollback probado;
- target runtime live;
- OLD preservado durante cutover;
- seguridad de acciones externas demostrada.

Mientras cualquiera falte, la decisión correcta es mantener OLD inactivo y preservado.
