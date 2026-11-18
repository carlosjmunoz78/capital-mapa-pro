# NEWS001 · Links audit WP PROD · 18/11/2026

Verificación **solo lectura** con el conector WordPress `wp_list_posts(post_type=page,status=publish)`, 100 páginas en página 1 y 66 en página 2. Confirmadas 8/8 URLs de navegación principales presentes como páginas **publicadas** con sus permalinks exactos.

B2C: `/hipotecas/hipoteca-90/`, `/antes-de-reservar/`, `/gastos-compra/`, `/pre-ok-hipotecario/`.
B2B: `/inmobiliarias/evitar-operaciones-caidas/`, `/inmobiliarias/calculadora-preanalisis-hipotecario/`, `/inmobiliarias/preok-hipotecario/`, `/inmobiliarias/formacion-inmobiliarias/`.

Los enlaces mailto de pregunta no son páginas WP y se verifican por patrón solamente. **No confundir `published` con HTTP 200 en cada cliente**: la ruta `hipoteca-90` fue abierta previamente con éxito en web, las demás devolvieron cache miss del buscador; la prueba de entrega final será E2E en navegador/mailbox. No modificar WP PROD. El motor ya genera 13 enlaces por newsletter y sus 10 bloques y logotipo (GitHub run 44280104275). El estado de NEWS001 envíos y suscripciones reales sigue OFF.

Esta prueba de enlaces es una puerta adicional de publicación, no autorización para enviar.
