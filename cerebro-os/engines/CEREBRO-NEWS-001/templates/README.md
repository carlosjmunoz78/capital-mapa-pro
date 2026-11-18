# CEREBRO-NEWS-001 · Diseño nuevo de newsletters Brevo · 18/11/2026

## Dos plantillas NUEVAS; ningún boletín antiguo reutilizado
- **Inmobiliarias**: `templates/news001_b2b_original_lab.html`; marca editorial “Inteligencia inmobiliaria”; contenido original de ejemplo orientado a facilitar operaciones hipotecarias. Fuentes/cifras semanales todavía no incluidas ni inventadas.
- **Particulares**: `templates/news001_b2c_original_lab.html`; marca editorial “Hipotecas sin vueltas”; contenido original de ejemplo sin prometer aprobaciones ni tipos hipotecarios ficticios.
- **HTML responsive** de 620px, estilos en línea, preheader, jerarquía, CTA, pie legal y placeholders oficiales de Brevo `{{ unsubscribe }}` / `{{ mirror }}`. Ref: https://help.brevo.com/hc/es/articles/209553645-Insertar-un-enlace-de-cancelaci%C3%B3n-de-suscripci%C3%B3n-personalizado-en-tus-emails
- Se han evitado todas las imágenes en el diseño LAB hasta disponer de imágenes UMS-001 con QA visual realmente aprobado. No hay publicaciones ni correo a clientes.
- Colores y tipografías son **candidatos**, no se ha comparado todavía pixel a pixel con el Manual de Marca de Fénix Capital. No afirmar BRAND_QA_PASS.
- El botón por ahora enlaza a la portada oficial; enlaces profundos por persona y fuente se sustituirán después de verificarlos y validar atribución UTM.
- Los textos de la edición concreta se generarán desde fuentes actuales verificadas, se revisarán bajo tribunal, y no copiarán contenido de newsletters antiguas. El texto demo de estas plantillas es original pero NO es la edición semanal final.
- **NO SE AUTORIZA ENVÍO:** las plantillas incluyen marcador de laboratorio en comentario HTML y deben pasar QA, reemplazo por contenido actual y eliminación del marcador antes del primer envío. Nunca convertir plantillas de laboratorio automáticamente en campañas públicas.
- B2B: candidato todo el histórico de inmobiliarias del Brevo, excluir la inmobiliaria **Salinas** y todas las bajas/rebotes/bloqueos, deduplicar y conservar evidencia.
- B2C: solo nuevos leads desde el momento efectivo de activación, desde web o cualquier formulario verificado en RRSS, con consentimiento explícito y registrado. Excluir absolutamente los particulares antiguos de Brevo.
- Sender domain DNS Brevo DKIM presente según auditoría Cloudflare; estado del dominio en panel Brevo y entrega real todavía por certificar.
- No crear listas ni modificar formularios/CRM/WordPress PROD. Coste adicional 0 €.

## Paleta contrastada con Manual de Marca Fénix Capital 2025 (página 5)
Solo: negro #222222, morado #870064, amarillo #FFB71B, naranja #FF5F00; blanco de soporte #FFFFFF. El prototipo anterior usaba incorrectamente azul/dorado. Corregido en LAB el 18/11/2026. La página 6 restringe Montserrat al logotipo: para texto general se mantiene tipografía estándar de correo electrónico, sin adjuntar ni distribuir archivos de fuentes. El rótulo HTML de marca no sustituye la verificación del logotipo vectorial oficial. Se mantiene NO SEND hasta QA editorial, consentimiento, entregabilidad e imagen aprobada.
