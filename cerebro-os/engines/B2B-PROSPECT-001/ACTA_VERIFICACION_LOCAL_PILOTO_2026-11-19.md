# B2B-PROSPECT-001 · ACTA DE VERIFICACIÓN LOCAL PILOTO · 2026-11-19

**Entorno:** LAB. **Estado:** PARCIAL (piloto acotado, no censo exhaustivo).  
**Método:** Notion fuente existente → SQL solo lectura → fuentes públicas locales/web oficial → alta mínima de candidatos → actualización municipal → SQL de comprobación.  
**Política:** no tocar PROD/App/CRM/NEWS-001, ni envíos, ni listas Brevo. Coste adicional contratado: 0 €.

## Baseline verificado de Notion
- Directorio: 4.560 fichas / 4.558 claves únicas / 2.789 con email / 4.354 con teléfono.
- 784 municipios: 309 con al menos una ficha y 475 sin ficha.
- 2 claves históricas repetidas (4 filas ya marcadas DUPLICADO_REVISAR): InmoCampo y Inmobiliaria Reina Victoria, ambas de Córdoba capital. No borrar ni fusionar sin comparar sus datos de CRM.
- 18 COLABORADOR_PROTEGIDO; 25 REACTIVACION_REVISAR; todos los registros comerciales mantenían Autorización comercial=NO_VERIFICADA.
- STYLO10 se encontró protegida como colaboradora en El Carpio; aunque dispone de oferta en Bujalance, no se duplicó ni alteró su tratamiento comercial.

## Altas controladas en la base existente
1. **Inmobiliaria Dr. Fleming (Bujalance, INE 14012)**: web propia https://inmobiliariafleming.es/ confirma actividad, dirección Avenida Doctor Fleming 18 B, teléfono +34 645 26 42 41 y correo inmofleming@gmail.com. Ficha Notion: https://app.notion.com/p/41d81b1a756d811bb858cc712ee95822. Estado PROSPECTO_REVISAR, autorización NO_VERIFICADA. Comprobación independiente de presencia municipal **VERIFICADO**, sin afirmar exhaustividad.
2. **INMOVILLA 2003 SL / INMOVILLA (Villa del Río, INE 14066)**: fuentes https://www.qdq.com/inmovilla-705323 ; https://infonif.economia3.com/telefono-direccion/cordoba/inmovilla-2003-sl ; directorio municipal histórico https://villadelrioes.blogspot.com/p/servicios.html . Dirección Blas Infante 5, 957 177 730. **No se ha comprobado vigencia del negocio**: candidato PROSPECTO_REVISAR, autorización NO_VERIFICADA; municipio sigue con Comprobación independiente=PENDIENTE. Ficha: https://app.notion.com/p/41d81b1a756d81cda094d69a18f131e4.

## Resultado físico post-escritura
Consultas SQL sobre fuentes Notion confirmaron:
- **4.562 fichas**, **4.560 claves distintas**, **2.790 con email**, **4.356 con teléfono**.
- **311 municipios CON_AGENCIAS** y **473 SIN_FICHAS_EN_FUENTES**.
- Solo 1 municipio marcado VERIFICADO en la nueva prueba, Bujalance; Villa del Río queda PENDIENTE.
- En ninguno de estos registros se autorizó ninguna campaña ni hubo importación a Brevo.

## Limitaciones
- Dos altas no equivalen al cierre de los 146 municipios objetivo Córdoba→Jaén→Sevilla ni a los 475 de toda Andalucía.
- Solo la existencia/actividad de Dr. Fleming está contrastada en su web. Teléfonos y emails no fueron probados mediante interacción; publicar un email no acredita consentimiento comercial.
- Mantener separados *ficha localizada*, *actividad vigente confirmada* y *autorización de contacto*. El valor municipal CON_AGENCIAS indica detección, no censo completo.

## next_block
1. Revisar ambos pares históricos duplicados preservando el original y las exclusiones.
2. Ampliar verificación local de los **40 municipios cordobeses todavía SIN_FICHAS_EN_FUENTES**, antes de Jaén (44) y Sevilla (60), priorizando fuentes oficiales y webs corporativas.
3. Alta solo cuando se haya comprobado en Notion que no existe clave/negocio equivalente, con procedencia, fecha y estado NO_VERIFICADA.
4. Conservar CRM PROD y Brevo sin modificación, y exigir gate comercial/privacidad para cualquier envío.


## Conciliación documental adicional (sin borrado)
Se inspeccionaron las cuatro páginas de los dos pares duplicados y se dejó anotado en cada una el vínculo a su pareja y la ficha candidata que conserva más información, **sin alterar el tratamiento DUPLICADO_REVISAR**.
- InmoCampo: el registro con teléfono +34 654 066 633 conserva Estado anterior «No llamado»; su par no tiene teléfono y muestra igualmente «No llamado».
- Inmobiliaria Reina Victoria: el registro con teléfono +34 957 201 259 muestra Estado anterior «Sin revisar», mientras el par sin teléfono dice «No llamado». **Diferencia histórica relevante; no fusionar automáticamente.**
- Ambas parejas siguen pendientes de cotejo de identidad y estado con el CRM de origen en modalidad solo lectura; en indicadores deduplicados cuentan una vez por Clave.


## Ampliación en la misma sesión · Nueva Carteya
- **Inmobiliaria Fernández**, Nueva Carteya, INE 14046: Habitaclia y Fotocasa confirman agencia con cartera de 4 inmuebles, dirección Francisco Merino 60, +34 695 470 805 y rafegeser@gmail.com. Ficha: https://app.notion.com/p/41d81b1a756d815e9947e1120c6812f4.
- Municipio actualizado de 0 a 1 agencia y a VERIFICADO por existencia (NO exhaustividad).
- Consulta SQL de cierre: **4.563 fichas**, **4.561 claves distintas**, **2.791 con correo**, **4.357 con teléfono**. **312 municipios con al menos una ficha**, **472 sin ficha**, **2 municipios con comprobación independiente VERIFICADO** (Bujalance, Nueva Carteya), **Villa del Río pendiente de comprobar vigencia**.
- Primera ruta pendiente ahora: Córdoba **39** municipios sin fichas; Jaén **44**; Sevilla **60**, suma **143**. No se activan campañas ni se modifican CRM/NEWS-001/PROD.
