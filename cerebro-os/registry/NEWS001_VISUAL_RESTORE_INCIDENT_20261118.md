# INCIDENTE VISUAL NEWS001 · 18/11/2026 · CORRECCIÓN USUARIO

Estado: **RECHAZADO el diseño simplificado de LAB** (se comprobó primero la paleta pero NO la fidelidad visual).

## Evidencia real abierta en el archivo original aportado
Fuente: `CEREBRO_NEWS_001_PRUEBA_DOS_NEWSLETTERS_20261117.zip`, generada en LAB el 17/11/2026. Contiene editor, HTML completo B2B y B2C, pruebas, imágenes y PNG de escritorio/móvil. No es la serie histórica de campañas antiguas enviadas en Brevo. No reutilizar campañas antiguas.

**Antes (NO VÁLIDO):** `cerebro-os/engines/CEREBRO-NEWS-001/templates/news001_{b2b,b2c}_original_lab.html` como estaba el 18/11: apenas 3 secciones de contenido, 0 imágenes, ningún logotipo auténtico, título de marca tecleado, botón morado casi rosa. El anterior test de "calidad" comprobaba que NO hubiera ninguna imagen: un grave error del criterio de aceptación. Pasar colores de marca no prueba completar un diseño.

**Referencia correcta (restaurada en archivo LAB LOCAL):** plantillas originales autocontenidas (`NEWS_FENIX_b2b_ABRIR_SIN_INTERNET.html`, `NEWS_FENIX_b2c_ABRIR_SIN_INTERNET.html`) con logotipo Fénix original, imagen de cabecera para cada audiencia, 1 H1, 8 H2, 13 enlaces, 10 módulos de comunicación por audiencia, textos extensos, semáforo/checklists, noticias y recursos, CTA, redes, pie legal y baja. Fondo claro, acento naranja corporativo `#FF5F00` y negro. No utilizar botón morado como principal en esta composición. Móvil y escritorio revisados en Chromium: 2/2 imágenes cargadas cada uno, overflow horizontal 0, alturas 4003/4722 B2B y 3880/4445 B2C.

Hashes exactos de fuentes HTML ZIP:
- B2B SHA256 `7a089bd9d071fa31e99e41389593b10a6179fb1e93e3860ea5534e6687ebfb75`
- B2C SHA256 `4946ebe5437629924aa458f3f3fd93c396b55d1115a9c3ca437498310eaea4d3`
- ZIP LOCAL restaurado `NEWS001_DISENOS_COMPLETOS_RESTAURADOS_20261118.zip` SHA256 `0558a62273853b86a79b1ae49cc76b1523e85e67ef5743120034456802042311`

## PREVENCIÓN
- Marcar en registro los dos archivos HTML simplificados GitHub como `SIMPLIFIED_CANDIDATES_REJECTED`. No son diseños canónicos. El archivo restaurado reside de momento en el artefacto local entregado al usuario, **NO** está publicado en GitHub, Brevo, WordPress ni PROD; no simular promoción.
- Tests GitHub deben registrar rechazo/fail-closed; al pasar a `VISUAL_ACCEPTED`, exigir al menos 2 imágenes reales cargables (incluido logo gráfico auténtico), 8 H2, 13 enlaces, coherencia de la composición escritorio/móvil, texto y 10 módulos, no solo tonos corporativos.
- Para Brevo, el HTML autocontenido sirve de preview; antes del email real, alojar imágenes correctamente (no data URI), verificar enlaces públicos y compatibilidad real con Gmail/Outlook/Brevo; copyright/licencias, edad de fuentes, datos Euríbor y pie legal, consentimiento DOI y baja. Los borradores Brevo separados están etiquetados `NO_ENVIAR` mientras no se verifiquen las URLs externas.

**No se ha modificado contacto alguno, ni enviado newsletter, ni escrito CRM/App/WordPress PROD. No coste adicional.**

## CIERRE DEL FALLO DE REPRODUCCIÓN VISUAL · 18/11/2026
Tras localizar los originales, se han colocado TODOS los módulos reales de CEREBRO bajo `cerebro-os/engines/CEREBRO-NEWS-001/editor/`, incluyendo motor editorial, noticias/contrato, adaptador optativo, pruebas y tres recursos visuales originales preservados como base64 bit-exact. No se escribió en las maquetas simplificadas rechazadas.

Ejecución propia GitHub Actions run **44280104275**, workflow `NEWS001 · CEREBRO genera diseño completo LAB`, job `cerebro-reproduce-both-newsletters`: **SUCCESS**. Artefacto privado **14417215089**, contiene ambos borradores HTML Brevo, ambos previews y los tres assets. Los SHA256 de los tres assets pasaron. El motor produjo dos ediciones dinámicas con 10 bloques, 13 enlaces, 687 palabras B2C y 667 palabras B2B, y comprobó que puede sustituir textos de edición sin perder el diseño.

Se descargó el ARTEFACTO GENERADO POR GITHUB (no el ZIP original previo) y se renderizaron en Chromium dos newsletters x escritorio/móvil; imágenes **2/2 cargadas cada una**, overflow horizontal false, altura B2B 4003/4722 y B2C 3880/4445. Se comparó visualmente con la composición original completa: imágenes, logo, secciones, CTA y footer restituidos. Una plantilla vacía con 3 secciones no puede sustituir este motor.

**Qué NO significa:** no hay comprobación de contenido semanal futuro ni actualización automática de fuentes; no hay envío, QA de clientes de email ni consentimiento B2C acreditado; Brevo PROD sigue OFF; no promoción desde LAB a producción. Compromiso: no sustituir el editor canónico por rediseños parciales ni aprobar una paleta sola como QA visual. 
