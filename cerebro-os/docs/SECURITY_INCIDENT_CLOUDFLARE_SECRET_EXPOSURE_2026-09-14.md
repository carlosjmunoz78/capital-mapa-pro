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
- Una segunda auditoría se limitó a **metadata de Workers**, sin leer bindings ni secretos. Encontró dos scripts (`fenix-capital-inmo-map` y `fenix-capital-inmo-maps`), ambos sin rutas declaradas en la respuesta y con observabilidad/logs persistentes habilitados.
- No se encontró ningún otro escenario Make cuyo nombre contenga `Cloudflare`; el escenario temporal de inventario es el único resultado actual de esa búsqueda.

## Contención aplicada

- El escenario `9773361` de inventario Cloudflare fue desactivado inmediatamente tras la lectura sensible.
- No se repitió el endpoint de Pages que había devuelto el valor sensible.
- Para ampliar inventario se creó el escenario temporal read-only `9803917`, exclusivamente para listar metadata de Workers. Fue ejecutado con éxito y posteriormente desactivado. No modifica Cloudflare.
- No se persistió el secreto en CEREBRO.
- No se rotó automáticamente: rotar sin mapa de dependencias podría romper un consumidor no inventariado.
- No se modificó Cloudflare, DNS, GitHub Pages ni la App.

## Conclusión de routing

La incertidumbre sobre el papel de Cloudflare Pages queda cerrada: **no es el canal canónico de `app.fenixcapital.es`**. Se conserva intacto como superficie paralela/no canónica para no romper posibles dependencias históricas. Su configuración de build explica además por qué no debe usarse como evidencia de salud de la App Vite.

## Gate de cierre del incidente

Antes de declarar el incidente cerrado:
1. Completar inventario de consumidores de la variable sensible dentro de Cloudflare sin volver a exponer su valor.
2. Preparar rollback/config snapshot.
3. Rotar el secreto por un canal autorizado sin escribir el valor en documentación o chat.
4. Revalidar cualquier consumidor.
5. Confirmar que GitHub Pages/App PROD sigue verde.
6. Marcar el secreto anterior como retirado.

Hasta entonces SECURITY global permanece abierto y no se permite retirada de privilegios legacy ni promoción autónoma final.
