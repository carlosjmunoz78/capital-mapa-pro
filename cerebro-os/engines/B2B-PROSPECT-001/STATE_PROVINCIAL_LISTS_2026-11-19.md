# B2B-PROSPECT-001 · STATE DIRECTORIO PROVINCIAL · 19-11-2026

## HECHO
- Origen cruzado, **solo lectura**: Supabase CRM Fénix PROD (**401** agencias no sintéticas, Córdoba 248 y Jaén 153); bases Notion histórica Córdoba (**109**), Inmobiliarias Todas (**108**) y maestro canónico Notion (**405**). La mayoría de registros históricos son duplicados, NO se suman sin reconciliación.
- Directorio SEPARADO Notion creado y **415 fichas incorporadas físicamente**: https://app.notion.com/p/41d81b1a756d8164b829f8357e36673a
- Ocho vistas filtradas por provincia en el mismo directorio; **no se han movido ni modificado** bases originales.
- Distribución: Córdoba **248**, Jaén **153**, Málaga **3**, Sevilla **3**, Granada **2**, Cádiz **2**, Almería **2**, Huelva **2**.
- Contactos actualmente incorporados: Córdoba 140 emails / 196 teléfonos, Jaén 31/100, Sevilla 3/3, Málaga 0/3, Granada 0/2, Cádiz 0/2, Almería 1/2, Huelva 0/2. Cifras con campos, NO emails comercialmente habilitados.
- **25 fichas NO QUIERE históricas** conservadas como `REACTIVACION_REVISAR` (Córdoba 16, Jaén 9), NO consideradas consentimientos. **18 colaboradoras activas** etiquetadas `COLABORADOR_PROTEGIDO`.
- Brevo Free: listas provinciales VACÍAS creadas en carpeta preexistente: Córdoba #25, Jaén #26, Sevilla #27, Málaga #28, Granada #29, Cádiz #30, Almería #31, Huelva #32. NEWS-001 listas #17/#18, campañas, automatizaciones y crons NO tocados.
- No se ha enviado publicidad, no se han realizado mutaciones CRM, no se han comprado datos ni suscripciones.
- 14 agencias de provincias no cubiertas por CRM incorporadas desde búsqueda pública local, con teléfonos y verificación progresiva de emails en webs corporativas. Es un **muestreo**, no cobertura de las seis provincias.

## PARCIAL / CALIDAD
- Hay **miles de fichas externas potenciales** en directorios de empresas y portales, pero sus totales NO son altas reales ni empresas únicas. Fuentes para revisar: https://www.idealista.com/agencias-inmobiliarias/, https://inmobiliarias.info/inmobiliarias-por-provincias/, https://www.thinkspain.com/es/directorio/andalucia/inmobiliarias
- Datos heredados de CRM/Notion contienen fechas y contactos desactualizables. La importación conserva fuente y estado anterior; emails/teléfonos de origen no implican validación de actualidad ni autorización para correo masivo.
- Revisión profesional: normalizar dominio, doble verificación de fuentes, consentimiento/legítimo interés aplicable y oposición; contactos que dijeron «no quiero» se mantienen como posible reactivación solo mediante vía lícita.
- Córdoba capital figura en directorio de legado, pero **no se ha insertado en el orden preferente de 15 tramos de contacto** (es distinto de conservar el historial).
- Los 8 listados Brevo sirven para futura segmentación, no para enviar campañas mientras las bajas, permisos y copy comercial no estén revisados.

## NEXT_BLOCK
Prospección **directa** de agencias por municipio y provincia mediante directorios y webs corporativas, extrayendo teléfono/email/web/municipio y fuente; deduplicar frente a las 415 fichas y ampliar el directorio Notion. Mantener el trabajo territorial en una sola cola, sin esperar crons ni fases y sin alterar NEWS-001 ni listas originales. **Antes de envíos comerciales**, aprobación editorial del propietario y gate legal/supresión.

## ACTUALIZACIÓN EJECUTADA 19-11-2026 · CONTACTOS REALES RECUPERADOS
- Notion [directorio provincial privado](https://app.notion.com/p/41d81b1a756d8164b829f8357e36673a): **894 fichas creadas y verificadas mediante lectura**. **629** con campo Email; **769** con campo Teléfono. Son DATOS de contacto provenientes de CRM/Notion y fuentes abiertas, no contactos comercialmente autorizados.
- Carga incremental ejecutada: **365 fichas nuevas** del directorio de agentes [Andalucía Viviendas API](https://www.andaluciaviviendas.es/localiza-tu-api-portal-inmobiliario-api-andalucia.html) y [UNEXIA](https://unexiaandalucia.com/asociados/), tras cruce con las 415 existentes; después **114 adicionales** recuperadas del archivo histórico de UNEXIA. Fuente y estado no verificado conservados por ficha.
- Distribución: Córdoba **288** (178 email / 232 teléfono), Jaén **193** (71/140), Sevilla **150** (144/143), Málaga **91** (75/91), Granada **59** (57/58), Cádiz **68** (66/63), Almería **23** (18/21), Huelva **22** (20/21). Suma **894**.
- El directorio contiene **185 textos de municipio diferentes por provincia**; tras normalización INE, equivale a **172 municipios únicos de la ruta de 784**, más la capital cordobesa (no pertenece a la ruta) y alias territoriales. **612 municipios siguen sin cobertura positiva acreditada**. Sin contacto encontrado no significa inexistencia.
- Las fuentes públicas permiten encontrar oficinas/agentes reales, pero NO prueban vigencia de todas las fichas ni exhaustividad. Datos de UNEXIA incluyen anotaciones históricas desde 2016. No calificar estas fichas como validadas sin verificación de cada contacto.
- Un intento de ampliar con OSM Overpass devolvió HTTP 504, 502 y luego timeout en servidor alternativo, sin registros incorporables; **no se utilizaron proxies de pago ni reintentos indefinidos**.
- Seguridad: **NEWS-001 y sus listas #17/#18 intactos**; **Brevo provincias #25-#32 creadas pero vacías**, no se han importado contactos sin comprobar bajas/permisos; **0 emails enviados**, 0 suscripciones nuevas, CRM PROD solo SELECT, sin tocar App/CRM/WP/main/DNS.
- El filtro `REACTIVACION_REVISAR` conserva explícitamente históricos «NO QUIERE» sin darlos por consentidos; `COLABORADOR_PROTEGIDO` aparta 18 colaboradores activos; Salinas y oposiciones quedan fuera de activación comercial. Dos claves duplicadas del CRM fueron marcadas `DUPLICADO_REVISAR` en el directorio nuevo (no se borró su ficha de origen).

### Bloque de avance sin excusas
Se ha realizado la importación física de **479 fichas adicionales** dentro de esta misión. **No se ha terminado el barrido completo de los 784 municipios**. Próximo paso material: ampliar rastreo de agencias en los **612 municipios sin cobertura** mediante nuevos directorios por localidad, y verificar nombre/teléfono/email/URL antes de considerar apta una ficha. No ejecutar campañas sin permisos y revisión editorial.
