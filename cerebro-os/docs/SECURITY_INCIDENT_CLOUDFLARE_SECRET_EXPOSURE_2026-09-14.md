# SECURITY INCIDENT · Cloudflare read-only inventory secret exposure · 2026-09-14

## Estado

`HUMAN_REQUIRED: SECURITY_INCIDENT`

## Qué ocurrió

Durante una ejecución controlada del escenario read-only `9773361` (`TEMP · CEREBRO Cloudflare read-only inventory`), la respuesta del proveedor incluyó el **valor raw** de una variable sensible de Cloudflare Pages.

El valor no se copia ni se conserva en este documento, tests, registry ni changelog. Debe considerarse comprometido por haber aparecido en una salida de herramienta/chat.

## Alcance confirmado

- Proyecto Cloudflare Pages: `fenix-capital-inmo-map`.
- Dominios del proyecto: únicamente el subdominio `pages.dev` del proyecto; no aparece `app.fenixcapital.es` como custom domain.
- Source: GitHub, repo `carlosjmunoz78/fenix-capital-inmo-map`, production branch `main`.
- Preview deployments están deshabilitados; el deployment observado para la rama de auditoría fue `skipped` por esa política.
- La App real sigue usando GitHub Pages como canal canónico y el smoke PROD de la App permanece verde.
- `package.json` de la App usa Vite (`vite build`), mientras Cloudflare Pages está configurado con `next-on-pages`; se registra como configuración paralela/no canónica, no como canal de PROD de la App.
- Búsqueda read-only en el branch por defecto no encontró una referencia de código a `APP_SECRET`; esto reduce, pero no elimina, la posibilidad de consumidores externos.

## Contención aplicada

- El escenario de inventario Cloudflare fue desactivado inmediatamente tras la lectura.
- No se repitió una lectura que pudiera volver a exponer secretos.
- No se persistió el secreto en CEREBRO.
- No se rotó automáticamente: rotar sin mapa de dependencias podría romper un consumidor no inventariado.
- No se modificó Cloudflare, DNS, GitHub Pages ni la App.

## Gate de cierre

Antes de declarar el incidente cerrado:
1. Inventariar consumidores de la variable sensible en Cloudflare y automatizaciones conectadas.
2. Preparar rollback/config snapshot.
3. Rotar el secreto por un canal autorizado sin escribir el valor en documentación o chat.
4. Revalidar cualquier consumidor.
5. Confirmar que GitHub Pages/App PROD sigue verde.
6. Marcar el secreto anterior como retirado.

Hasta entonces SECURITY global permanece abierto y no se permite retirada de privilegios legacy ni promoción autónoma final.
