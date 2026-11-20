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


## B2B-PROSPECT-001 · Segunda tanda local · 2026-11-20
**Estado:** HECHO para ingesta auditada de 5 candidatos; PARCIAL para verificación independiente de municipio y exhaustividad.

### Altas en Notion (sin contactos comerciales)
| Municipio | Ficha | Evidencia | Comprobación independiente |
| --- | --- | --- | --- |
| Luque | [INMOLUQUE](https://app.notion.com/p/41d81b1a756d81d98386edf6412fe373) | Web propia https://inmobiliarialuque.com/ + https://agencias.selectra.es/14880, Carrera 45, teléfono de empresa publicado | VERIFICADO: presencia, no exhaustividad |
| Espiel | [Guadiato Gestión Inmobiliaria](https://app.notion.com/p/41d81b1a756d813b9136cc3144501c4a) | Web propia https://guadiatogestioninmobiliaria.es/contacto/ y cartera https://guadiatogestioninmobiliaria.es/inmuebles/, Ánimas 2, teléfono/email publicados | VERIFICADO: presencia, no exhaustividad |
| Santaella | [Gestiones Integrales e Inmobiliarias La Campiña](https://app.notion.com/p/41d81b1a756d8108a769dd8352af22c7) | https://gestoriascordoba.es/especialidad/inmobiliaria y BORME 2019; diferencia Calle Delicias 29 vs 30, actividad presente por comprobar | PENDIENTE |
| Doña Mencía | [Mencicasa](https://app.notion.com/p/41d81b1a756d81fbaba3f56028b58ddb) | https://www.todosbiz.es/mencicasa_3o-957-69-52-87 y https://cordoba.buscalis.com/inmobiliarias-dona-mencia; directorios, sin sitio propio ni prueba de actividad actual | PENDIENTE |
| Moriles | [Inmobiliaria Gestimor](https://app.notion.com/p/41d81b1a756d8140a520c87b4bbce22e) | https://www.yaencontre.com/inmobiliarias/inmobiliaria-gestimor-82886 + https://www.idealista.com/pro/inmobiliaria-gestimor/venta-viviendas/moriles-cordoba/; cartera visible, oficina física no confirmada | PENDIENTE |

Todas las 5 fichas nuevas = `PROSPECTO_REVISAR` + `Autorización comercial: NO_VERIFICADA`. Sin importación a Brevo, comunicaciones ni escritura al CRM.

### Recuento post-escritura · lectura directa de Notion
- **4.568 fichas**, **4.566 claves distintas** (persisten los dos pares de duplicados históricos), **2.792 con email**, **4.361 con teléfono**.
- **317 municipios con al menos una ficha**, **467 municipios sin ficha**, de los 784.
- **4 municipios con evidencia independiente marcada VERIFICADO** en todo el directorio de municipios (Bujalance, Nueva Carteya, Luque, Espiel). Los demás continúan PENDIENTE.
- **Córdoba:** 42 con fichas / 34 sin fichas. **Jaén:** 53 / 44. **Sevilla:** 46 / 60.
- Primera ruta: **138 municipios aún SIN_FICHAS_EN_FUENTES** (34 + 44 + 60).
- Se han verificado acciones de alta y consultas SQL; no se afirma censo completo ni validación individual de teléfono/email.

### Precauciones metodológicas
No confundir **agencia que comercializa inmuebles en un municipio** con **oficina ubicada en ese municipio**. Fuentes secundarias pueden estar desactualizadas y el campo CON_AGENCIAS indica que existe una ficha candidata, no que sea definitivamente válida. Mantener `Comprobación independiente=PENDIENTE` salvo evidencia suficiente de presencia empresarial actual. No derivar permiso comercial de datos públicos.

### next_block
1. Continuar los **34 municipios de Córdoba** sin fichas, distinguiendo establecimiento local / cobertura desde otro pueblo / promotora no intermediaria.
2. Confirmar vigencia de Mencicasa, La Campiña, Gestimor e INMOVILLA 2003 SL antes de promover su estatus; descartar falsas coincidencias manteniendo trazabilidad.
3. Mantener protegidos colaboradores y reactivaciones, pares duplicados documentados, y las listas Brevo sin contactos.
4. Después verificar Jaén (44) y Sevilla (60), con entregas parciales auditadas.


## B2B-PROSPECT-001 · Tercera tanda local · 2026-11-20 (continuación)

**Alcance:** revisar fuentes locales en municipios cordobeses sin fichas; distinguir intermediarios con presencia actual de gestores mercantiles, promotoras, empresas municipales y agencias que solo anuncian propiedades en la zona. Todos los datos nuevos se han guardado exclusivamente en la base Notion de PROSPECTOS (NO ENVÍO), sin afectar CRM ni Brevo.

### Nuevas fichas (3) y comprobación
1. **Mar de Encinas · Cardeña (INE 14016)**. Web propia [quiénes somos](https://mardeencinas.es/sobre-nosotros) declara inicio en 2026 y base en Cardeña, [contacto](https://mardeencinas.es/contacto), y [anuncio profesional en Idealista](https://www.idealista.com/inmueble/112713212/) corrobora gestión/venta de vivienda en Cardeña. Teléfono +34 614 43 61 89 y email info@mardeencinas.es publicados en la web de negocio. [Ficha Notion](https://app.notion.com/p/41d81b1a756d81e6838bd0a89eb67b9f). `Comprobación independiente=VERIFICADO` **solo para presencia de negocio**, sin llamada ni visita física ni censo exhaustivo.
2. **Hermanos Caracuel Luque C.B. · Carcabuey (INE 14015)**. [Inmueble24](https://www.inmueble24.es/empresa-hermanos-caracuel-luque-en-carcabuey-42164) lo categoriza como agentes inmobiliarios y administradores de fincas en Obispo Pérez Muñoz 12. [eInforma](https://www.einforma.com/informes-empresas/CORDOBA/Carcabuey/Empresas-2.html) confirma denominación en el municipio. [Ficha Notion](https://app.notion.com/p/41d81b1a756d8129a497c5ec1cfa5aa0). `PENDIENTE` verificación de actividad, negocio abierto, contacto y mediación actual.
3. **San Acacio Gestiones Inmobiliarias S.L. · Montemayor (INE 14041)**. [Empresite](https://empresite.eleconomista.es/SAN-ACACIO-GESTIONES-INMOBILIARIAS.html) y [Kompass](https://es.kompass.com/v/montemayor/es_01_14_14041/) identifican sociedad de gestión inmobiliaria en San Acacio 11; no se obtuvo web ni oferta vigente. [Ficha Notion](https://app.notion.com/p/41d81b1a756d817fb61ddcbac4b62f1e). `PENDIENTE` confirmar servicio comercial actual y diferencia entre agencia y administración/tenencia.

Las tres fichas conservan `Tratamiento=PROSPECTO_REVISAR` y `Autorización comercial=NO_VERIFICADA`. Las tres páginas municipales anotan los vínculos y limitaciones; Carcabuey y Montemayor NO se promueven a verificado.

### Exclusiones analizadas (no insertar como agencia local)
- **HORDESA, Hornachuelos**: referencias del [Ayuntamiento](https://hornachuelos.es/ayuntamiento/catastro/) y [comisión liquidadora](https://hornachuelos.es/?p=6013) muestran empresa pública municipal, no agencia B2B privada corriente; no crear falso prospecto.
- **Villarejo Siglo XXI SL, Pedro Abad**: la [ficha mercantil](https://cincodias.elpais.com/directorio-empresas/empresa/1145930/villarejo-siglo-xxi) describe promoción/construcción, no intermediación residencial externa probada; no añadir como agencia de captación.
- **Andalusí Brokers 1492 SL**: aunque hay directorios que la atribuyen a Carcabuey, [EmpresaSite](https://empresite.eleconomista.es/ANDALUSI-BROKERS-1492.html) y [Cylex/Firmania](https://firmania.es/priego-de-cordoba/andalus%C3%AD-brokers-1492-1839024) sitúan su sede en Carretera Zagrilla, **Priego de Córdoba**, por lo que no se asigna falsamente a Carcabuey.
- **Agropisar**: la [guía oficial de Guadalcanal](https://www.guadalcanal.es/es/municipio/guia-local/empresas/Agropisar-S.L./) documenta actividad/localización sevillana; aparición en un agregador de Fuente Obejuna no basta para confirmar oficina cordobesa.
- **Seriedad Inmobiliaria Lainez**: publica propiedades en Bélmez, pero no consta en esta revisión que tenga oficina allí. No convertir cartera fuera de localidad en oficina.
- **Gestimor (Moriles)**: [Idealista](https://www.idealista.com/pro/inmobiliaria-gestimor/) y [Yaencontre](https://www.yaencontre.com/inmobiliarias/inmobiliaria-gestimor-82886) muestran cartera activa; no se confirmó oficina física. Sigue PENDIENTE.
- **Mencicasa / La Campiña / INMOVILLA**: resultados localizables en fuentes secundarias o mercantiles, pero persisten dudas de vigencia, ubicación y/o tipo de servicio. Ninguna se eleva a `VERIFICADO` por ese solo hecho.

### Lectura SQL posterior de Notion
- `fichas = 4.571`, `COUNT(DISTINCT Clave) = 4.569`, `con_email = 2.793`, `con_telefono = 4.362`.
- `CON_AGENCIAS = 320` municipios, con `VERIFICADO=5` (presencia, no exhaustividad) y `PENDIENTE=315`.
- `SIN_FICHAS_EN_FUENTES = 464` municipios; la ausencia de ficha NO confirma ausencia de agentes.
- Córdoba: **45 con fichas / 31 sin fichas** (76 de ruta); Jaén: **53 / 44**; Sevilla: **46 / 60**.
- Ruta prioritaria restante sin fichas: **135 municipios** (31 + 44 + 60). Baseline anterior: 138. No se reescribieron claves/estados históricos ni se eliminaron registros duplicados.

### Gate y siguiente bloque
- **0 campañas lanzadas**, 0 nuevos contactos importados en Brevo, sin activar NEWS-001 ni comunicaciones; sin cambios en App/CRM PROD, WordPress, DNS o main. No se contrató servicio adicional.
- **next_block:** revisar municipios cordobeses restantes priorizando fuentes oficiales, webs propias y establecimientos físicamente atribuibles; separar localización de agentes que solo comercializan inmuebles en la zona; no declarar exhaustividad. Preparar verificación no invasiva de candidatos pendientes. Después Jaén y Sevilla.


## B2B-PROSPECT-001 · Cuarta tanda local · 2026-11-20

**Ámbito:** investigación de los 31 municipios cordobeses que aún figuraban `SIN_FICHAS_EN_FUENTES`. Se realizó contraste dirigido de fuentes municipales, buscadores, portales inmobiliarios y BORME (consultado en texto HTML). A las fichas activas se aplicó búsqueda previa de duplicados en Notion. **Resultado: 5 fichas candidatas nuevas / 5 municipios de fuentes ampliadas / 0 nuevos municipios con presencia comercial independiente acreditada.**

### Altas auditadas en Notion
| Municipio (INE) | Nueva ficha | Evidencia y clasificación |
| --- | --- | --- |
| Pedroche (14051) | [InmoPedroche S.C.P.](https://app.notion.com/p/41d81b1a756d8112bdebedd6fce67f82) | Blog propio https://inmopedroche.blogspot.com/ con anuncios de 2016–2018; denominación en https://www.einforma.com/informes-empresas/CORDOBA/Pedroche.html y https://www.axesor.es/Informes-Empresas/n/7326706/INMOPEDROCHE_SCP.html ; contacto en Vymaps no contrastado (625 525 722); direcciones diversas entre fuentes. **HISTÓRICO / PENDIENTE vigencia 2026**. |
| Hornachuelos (14036) | [SMRG Propiedades S.L.](https://app.notion.com/p/41d81b1a756d81fbabf1e7ace3c617da) | [BORME 2024](https://www.boe.es/diario_borme/txt.php?id=BORME-A-2024-233-14) y [Empresia](https://www.empresia.es/empresa/smrg-propiedades/): Calle San Calixto 47, CNAE 68.32; no demuestra agencia intermediadora activa. **MERCANTIL / PENDIENTE**. |
| Obejo (14047) | [Agrogestión y Derecho S.L.](https://app.notion.com/p/41d81b1a756d81f19c73f44484f09c02) | [BORME 2024](https://www.boe.es/diario_borme/txt.php?id=BORME-A-2024-58-14) y [Empresia](https://www.empresia.es/empresa/agrogestion-y-derecho/): Media Luna 22, Obejo (Cerro Muriano), objeto incluye actividades inmobiliarias por cuenta de terceros. **MERCANTIL / PENDIENTE actividad**. |
| La Victoria (14065) | [InvTur](https://app.notion.com/p/41d81b1a756d812c91ceddafba6ccc6b) | [LinkedIn empresa](https://es.linkedin.com/company/invtur) y [directorio de referencia](https://nova-inmobiliaria.es/invtur/) identifican gestión inmobiliaria **turística** en Clara Campoamor 12, La Victoria; no prueban oficina residencial activa ni actividad en 2026. **TURÍSTICA / PENDIENTE**. |
| Montalbán de Córdoba (14040) | [DC Patrimonial S.L.](https://app.notion.com/p/41d81b1a756d8131a8b4c239260af0a1) | [BORME 2026](https://www.boe.es/diario_borme/txt.php?id=BORME-A-2026-42-14) / [Empresia](https://www.empresia.es/empresa/dc-patrimonial/): constituida en febrero 2026, La Encina 16, objeto incluye compraventa, alquiler e intermediación. **MERCANTIL / PENDIENTE prueba de actividad real**. |

En las cinco páginas municipales se conserva `Comprobación independiente=PENDIENTE`. El contador `CON_AGENCIAS` significa **hay una ficha candidata**, no que esté verificado establecimiento abierto, intermediación operativa ni exhaustividad. Cada nueva ficha tiene procedencia, fecha, `PROSPECTO_REVISAR` y `Autorización comercial=NO_VERIFICADA`.

### Casos descartados / prevención de falsos positivos
- Portales Idealista, Fotocasa, Yaencontre o SoloCasa pueden mostrar una **agencia que comercializa un inmueble del municipio pero tiene oficina en otro lugar** (Lainez en Peñarroya, API Pérez Escribano en Castro del Río, etc.). No crear falsas oficinas locales.
- El listado https://nova-inmobiliaria.es/category/villanueva-del-duque incluye una granja avícola y alojamientos rurales bajo paraguas inmobiliario: **no equivale a siete agencias inmobiliarias**.
- Los resultados sobre **Pérez & Alcaraz** corresponden a Palma del Río, no a Montalbán; [web propia](https://www.perezalcaraz.com/sobre-nosotros/).
- **Gestiones Inmobiliarias Silper S.L.** aparece en directorios de Montalbán pero está incluida en la [resolución BOE-A-2022-14753 de revocación de NIF](https://boe.es/diario_boe/txt.php?id=BOE-A-2022-14753) para B14694491. Es antecedente jurídico histórico, **no prueba de estado actual**, y no se incorpora sin comprobación jurídica y comercial posterior.
- **Promotoras / tenedoras / gestorías** requieren clasificación diferenciada, no atribuirles automáticamente mediación inmobiliaria de terceros.

### Cierre con consultas SQL directas a Notion
- Directorio: **4.576 fichas**, **4.574 claves únicas**; **2.793 con email**, **4.363 con teléfono**. Persisten las 2 claves históricas duplicadas sin borrar.
- Distribución tratamiento/permiso: **4.529 PROSPECTO_REVISAR**, **25 REACTIVACION_REVISAR**, **18 COLABORADOR_PROTEGIDO**, **4 DUPLICADO_REVISAR**; todas con autorización `NO_VERIFICADA` según consulta de estado.
- Municipios: **325 CON_AGENCIAS (320 PENDIENTE + 5 VERIFICADO)**, **459 SIN_FICHAS_EN_FUENTES**, total **784**.
- Primera ruta pendiente: **Córdoba 26**, **Jaén 44**, **Sevilla 60** municipios sin ficha. Total **130**, de los cuales Córdoba bajó 31→26.
- Todas las nuevas fichas y cinco páginas municipales comprobadas mediante respuestas de escritura y SELECT de Notion; cifras confirmadas contra la base, no proyecciones.

### Seguridad y próximos pasos
- CEREBRO LAB: ninguna modificación de CRM PROD, App, WordPress, DNS, main ni NEWS-001. **0 campañas**, **0 contactos añadidos a Brevo** por esta operación; sin contratación de nuevas suscripciones.
- **next_block:** completar búsqueda focalizada de los 26 municipios cordobeses sin fichas, pero priorizar de forma creciente **calidad/vigencia por encima de cantidad**; revisar y desambiguar estos 5 candidatos más los anteriores con `PENDIENTE`. No promover un municipio a `VERIFICADO` sin evidencia comprobable de negocio actual. Luego Jaén→Sevilla.


## B2B-PROSPECT-001 · Quinta tanda · Control de calidad y no duplicación · 2026-11-20

**Objetivo:** priorizar calidad de prospectos B2B antes de nuevas altas. Ejecutado contraste web/nombres/sedes, cotejo con Notion de empresa existente, notas de procedencia y actualización de fichas **sin cambiar claves, tratamientos, denominaciones ni recuentos**. No se ha modificado PROD, CRM, listas Brevo ni NEWS-001.

### Resultado verificable: 8 páginas de Notion ampliadas
1. [OcasiónCasa Peñarroya — ficha existente](https://app.notion.com/p/41d81b1a756d81c092c3d4585436471f): se enlaza [perfil Julio León Tejero en Idealista](https://www.idealista.com/pro/julioleontejero/) que declara dirección Av. Universidad 12, 14240 Belmez, [anuncio de Belmez](https://www.idealista.com/inmueble/112241742/) que identifica a **OcasiónCasa Oficina Peñarroya** y el número 957 567 018 **ya registrado**. También [reseñas de la oficina](https://agenciasinmobiliarias.com.es/es-es/i/11446-ocasion-casa/) citan a Julio y ventas en Belmez. **Decisión:** probable agente comercial/equipo OcasiónCasa, no dar de alta una segunda inmobiliaria sin evidencia de sede jurídica/operativa separada. Conservar datos Overture originales.
2. [Municipio Belmez](https://app.notion.com/p/41d81b1a756d81aabb17c10aede44b34): revisión documentada; anuncios en la zona y perfil con dirección Belmez **no prueban oficina B2B independiente**. Se conserva 0 fichas de negocio local único y `PENDIENTE`, con pista para verificación física posterior.
3. [Inmobiliaria Gestimor](https://app.notion.com/p/41d81b1a756d8140a520c87b4bbce22e): [Yaencontre](https://www.yaencontre.com/inmobiliarias/inmobiliaria-gestimor-82886) muestra 19 anuncios y [piso de Moriles actualizado 20/10/2026](https://ca.yaencontre.com/venda/pis/immoble-82886-112853464). **Actividad anunciante en 2026 confirmada, sede exacta Moriles no confirmada**. Sin teléfono inventado.
4. [Municipio Moriles](https://app.notion.com/p/41d81b1a756d810bb702c639c96c1083): diferencia actividad en municipio vs establecimiento residente; conservado `PENDIENTE`.
5. [Gestiones Integrales e Inmobiliarias La Campiña](https://app.notion.com/p/41d81b1a756d8108a769dd8352af22c7): [BORME](https://www.boe.es/diario_borme/txt.php?id=BORME-A-2019-119-14) y [Cinco Días](https://cincodias.elpais.com/directorio-empresas/empresa/8566908/gestiones-integrales-e-inmobiliarias-la-campina) ubican domicilio social **Delicias 30, Santaella**, mientras directorios como [Gestoría Leal](https://gestorialealvilches.es/gestiones-integrales-e-inmobiliarias-la-campina/) ubican atención comercial en **Delicias 29**. **No sobreescribir una dirección por otra sin comprobar ambas**. No consta cartera propia reciente ni intermediación residencial actual verificada.
6. [Municipio Santaella](https://app.notion.com/p/41d81b1a756d81fb97f1cc684a199f9d): confirmación de conflicto direcciones 29/30 y calidad mercantil; permanece `PENDIENTE`.
7. [Municipio Espejo](https://app.notion.com/p/41d81b1a756d81cebc81f9c5b2320d28): [gestoría local](https://gestoriascordoba.es/municipio/espejo) no acredita actividad de agencia residencial; [Mubasol de Espejo](https://www.boe.es/diario_borme/txt.php?id=BORME-A-2023-140-14) es principalmente solar/energía (CNAE 3519), no debe agregarse como agencia por compraventa accesoria; [Pérez Escribano](https://perezescribano.net/) opera desde Castro del Río pese a comercializar inmuebles en Espejo. **Cero altas falsas**.
8. [Municipio Fuente Obejuna](https://app.notion.com/p/41d81b1a756d81c7a660ca9257688ddb): [Idealista](https://www.idealista.com/agencias-inmobiliarias/fuente-obejuna-cordoba/inmobiliarias) enumera agencias que venden allí, pero ninguna demuestra oficina local a partir de ese directorio; OcasiónCasa Peñarroya ya inventariada. **Cero duplicaciones por zona de cartera**.

### Nueva disciplina de evidencia (documental, sin cambiar esquema Notion)
- **AGENCIA_LOCAL_VERIFICADA**: identificación de empresa + actividad de intermediación actual + base/establecimiento en municipio sustentado por fuentes. No equivale a censo municipal completo.
- **AGENTE_ASOCIADO / MISMA_RED**: profesional o perfil distinto vinculado a agencia ya existente; relacionar sin crear duplicado de empresa.
- **COMERCIALIZA_EN_MUNICIPIO**: anuncios actuales, pero sede empresarial está en otro lugar o sin verificar; conservar la cobertura como nota, no como oficina física local.
- **MERCANTIL_O_GESTORIA_PENDIENTE**: objeto CNAE/BORME o directorio de asesoría sin prueba de actividad efectiva residencial.
- **DESCARTADO_COMO_AGENCIA**: empresa ajena al negocio B2B de intermediación, por ejemplo energía solar o promotor por cuenta propia.
- **CONTACTO_COMERCIAL** separado: ni email público ni teléfono publicado demuestran base para campañas. Conservar `Autorización comercial=NO_VERIFICADA` y respetar `NO_CONTACTAR`, colaboradores y oposiciones.

### Cierre SQL Notion, sin alteración de contadores por diseño
- **4.576 fichas**, **4.574 claves distintas**; 2.793 fichas con email y 4.363 con teléfono.
- **325 municipios con ficha** (5 `VERIFICADO` de presencia, 320 `PENDIENTE`), **459 sin ficha**, 784 total.
- Pendientes `SIN_FICHAS_EN_FUENTES`: **Córdoba 26, Jaén 44, Sevilla 60**; total primera ruta **130**.
- No se crearon fichas nuevas en esta tanda ni se tocaron los 2 pares duplicados anteriores; todas las acciones de escritura fueron **append no destructivo** de evidencia en 8 páginas, con resultados aceptados por Notion.

### next_block
1. De los 26 municipios cordobeses aún sin ficha, priorizar nombres con **dirección empresarial en el municipio + cartera activa reciente**; si no existe evidencia, documentar resultado sin crear sociedades/inmobiliarias por CNAE genérico.
2. Verificar relación comercial y sede real de Julio León/OcasiónCasa; verificar sede Moriles de Gestimor y domicilios de La Campiña. No modificar estados de autonomía ni `VERIFICADO` hasta contraste independiente.
3. Priorizar la **lista deduplicada de agencias realmente operativas**, conservando referencias del histórico y sin campañas o altas de Brevo.
4. Mantener rama LAB, CRM/App/NEWS-001/PROD y recursos contratados sin alteración; gasto adicional contratado 0 €.


## 2026-11-20 · Decisión del propietario: simplificar barrido y segmentar Brevo por 8 provincias

**Orden solicitada:** ampliar directorio de inmobiliarias andaluzas mediante Páginas Amarillas y otras fuentes públicas, recolectando nombre y preferiblemente email/teléfono/dirección, usar 8 listas provinciales y segmentación por ciudad, después preparar campaña gráfica premium con variante provincial/municipal, enlaces locales, secuencia, límites por envío y control de entregabilidad.

**Hallazgo Brevo en vivo:** ya existen 8 listas vacías en carpeta 5, NO duplicar:
- Córdoba 25, Jaén 26, Sevilla 27, Málaga 28, Granada 29, Cádiz 30, Almería 31, Huelva 32.
- Listas NEWS-001 #17/#18 y contactos asociados sin tocar.
- Conector Brevo actual expone gestión de listas y `add_contact_to_list` solo para **contactos que ya existen**; no expone creación/importación general de contactos.

**Recuento exacto en Notion por provincia (SELECT 2026-11-20):**
| Provincia | Fichas | Fichas con email | Emails distintos por provincia | Con teléfono |
|---|---:|---:|---:|---:|
| Córdoba | 507 | 276 | 276 | 442 |
| Jaén | 252 | 107 | 105 | 197 |
| Sevilla | 635 | 410 | 410 | 624 |
| Málaga | 1711 | 1065 | 1065 | 1657 |
| Granada | 437 | 295 | 295 | 432 |
| Cádiz | 526 | 334 | 334 | 513 |
| Almería | 352 | 216 | 216 | 344 |
| Huelva | 156 | 90 | 90 | 154 |
| **Total** | **4576** | **2793** | **2791** (deduplicación dentro de provincia) | **4363** |

**GATE LEGAL/PROVEEDOR:** artículos 20–21 LSSI https://www.boe.es/eli/es/l/2002/07/11/34 y política Brevo https://help.brevo.com/hc/es/articles/213405965-Cree-una-base-de-datos-de-contactos-leg%C3%ADtima-para-lograr-una-entregabilidad-y-un-cumplimiento-%C3%B3ptimos . Brevo prohíbe **importar listas de direcciones copiadas de sitios públicos y directorios por scraping**, y exige listas legítimas; el email públicamente visible no acredita consentimiento ni excepción legal suficiente para campaña. En Notion, el campo `Autorización comercial` fue consultado: **0 VERIFICADA**. Por tanto no importar indiscriminadamente, no activar listas ni lanzar email masivo. Una relación contractual previa lícita y mensajes sobre servicios similares pueden requerir evaluación específica, incluida ausencia de oposición; no asumir cumplimiento de todas las fichas.

**Plan de ejecución simplificado, sin reabrir arquitectura:**
1. Fuente Páginas Amarillas de las 8 provincias, directorios oficiales/profesionales y webs de empresas; alta y dedupe en Notion por empresa+municipio+teléfono/dominio, con fecha, fuente, evidencia, y tipo de actividad. Capturar dirección cuando fuente la documente; no inventarla; distinguir oficina real de municipio donde vende.
2. Segmentación **8 provincias (listas existentes)** y atributo ciudad/municipio, para personalización local sin proliferar listas. Conector Brevo no crea atributos/contactos actualmente; resolver con capacidad ya disponible o importación lícita posterior.
3. Separar `IDENTIFICADA`/`VALIDADA`/`APTA_LEGAL_Y_BREVO`/`OPOSICION` para no mezclar mera captura con permisos de envío. Respetar 18 colaboradores protegidos, 25 reactivaciones históricas y oposiciones.
4. Solo para destinatarios cuya inclusión cumpla ley y Brevo: creatividad y copy premium provincial/local, enlace relevante por ciudad, desuscripción, SPF/DKIM/DMARC, límites y lotes supervisados.
5. No afirmar ni prometer bandeja Principal/Notificaciones de Gmail: el proveedor destinatario decide la pestaña; autenticación y reputación pueden mejorar entregabilidad, no forzar categoría.

**Estado de este bloque:** HECHO verificación ocho listas y métricas; DEFINIDO segmentación; POR HACER barrido extensivo adicional de Páginas Amarillas y enriquecimiento del directorio; BLOQUEADO por política del proveedor para importación de contactos públicos a campañas; 0 envíos y 0 cambios en contactos Brevo/CRM/App/PROD. Coste adicional 0€.


## 2026-11-20 · Barrido transversal Páginas Amarillas + webs + colegios · Lote 1

**Pedido del propietario:** ampliar el máximo directorio de agencias de toda Andalucía, con nombre, email preferentemente, teléfono y domicilio por empresa; conservar 8 listas provinciales de Brevo; decidir la cadena de correos más adelante. No es un proyecto de newsletters periódicas.

### Fuentes contrastadas
Se abrieron las ocho búsquedas provinciales de [Páginas Amarillas](https://www.paginasamarillas.es/a/inmobiliarias/), además de [UNEXIA asociados](https://unexiaandalucia.com/asociados/), [colegiados API en Jaén](https://www.foroempresarial.com/anuncios/buscadorcli3.asp?cliente=79887&valida=1), web corporativa de cada candidato y portales contrastivos. Los contadores de resultados de Páginas Amarillas son **resultados de categoría**, no agencias únicas:
- Córdoba: 658; Jaén: 300; Sevilla: 1.909; Málaga: 5.060; Granada: 1.038; Cádiz: 1.464; Almería: 857; Huelva: 463.
- Total categórico sin dedup: 11.749 resultados; algunos son gestores de fincas, promotoras, comercios de otra clase, servicios en la zona sin establecimiento y duplicados; nunca declarar estos resultados como empresas únicas ni sumar directamente a las 4.589 fichas.
- En UNEXIA, la mayor parte de los asociados contrastados ya tenían registro en Notion. **No duplicar**.

### 13 nuevas fichas guardadas en Notion, con localidad, procedencia y dirección en el contenido
1. [TAMAR Islantilla](https://app.notion.com/p/41e81b1a756d81da8013e76d2a5ec067), **Isla Cristina**, Huelva; web/cartera https://tamarislantilla.com/ y [BORME 2026](https://boe.es/diario_borme/txt.php?id=BORME-A-2026-58-21). **Corrección:** aunque la web usa CP 21449, el domicilio social vigente consta en Isla Cristina (21430) y Habitaclia confirma la dirección; se corrigió la ficha de Lepe a Isla Cristina y se ajustaron ambos contadores municipales.
2. [AC Inmorocío](https://app.notion.com/p/41e81b1a756d817392dbe2fc6e3a7728), Almonte (núcleo El Rocío), Huelva; web https://www.inmorocio.es/contacto.
3. [Apigestión Aljarafe](https://app.notion.com/p/41e81b1a756d8128881bfdef37369061), Gines, Sevilla; Páginas Amarillas y https://www.infobiliaria.es/inmobiliarias/sevilla/apigestion-aljarafe/.
4. [Gesem Inmobiliaria](https://app.notion.com/p/41e81b1a756d8124aff3c0bc358952d6), Almuñécar, Granada; web https://inmogesem.es/ y web de turismo local https://www.visitalmunecar.es/blog/empresas/gesem/.
5. [Quintamar Inmobiliaria](https://app.notion.com/p/41e81b1a756d8168a16bd5cd4b5e5c93), Torrox-Costa, Torrox, Málaga; web/aviso legal https://quintamar.de/contact.
6. [Tarifa Casas](https://app.notion.com/p/41e81b1a756d81f390fac27883ef4b9f), Tarifa, Cádiz; PA y Cylex (email sin confirmar en esta tanda).
7. [Tarifa Inmobiliaria](https://app.notion.com/p/41e81b1a756d81d6b222d211ba4ec45d), Tarifa, Cádiz; PA y Yaencontre, Calle Nuestra Señora de la Luz 14 (email sin confirmar).
8. [Inmobiliaria Báltico](https://app.notion.com/p/41e81b1a756d81ccb66be0b6423c03a5), Sevilla; PA/Cylex, Calle Mar Egeo 7 (email sin confirmar).
9. [ALM Proyectos e Inversiones](https://app.notion.com/p/41e81b1a756d81af9ee2e46b5484c364), Motril, Granada; PA y otro directorio con **direcciones distintas**, no imponer dirección única hasta contrastar.
10. [Aliservices Inmobiliaria Online](https://app.notion.com/p/41e81b1a756d810d9134c7a7e4bfff79), Aguadulce / Roquetas de Mar, Almería; PA y Cylex (email pendiente).
11. [Inmobiliaria Persson](https://app.notion.com/p/41e81b1a756d81f9b778d8783a13291e), Écija, Sevilla; web con oferta reciente https://www.inmobiliariapersson.com/ y correo visible en perfil profesional de Fotocasa.
12. [ALEA JPB S.L.](https://app.notion.com/p/41e81b1a756d816abf1ec4bd1f7832b1), Torredonjimeno, Jaén; PA https://www.paginasamarillas.es/f/torredonjimeno/alea-jpb-s-l_229496153_000000001.html, localización a reconciliar.
13. [Inmobiliaria AG (Baena)](https://app.notion.com/p/41e81b1a756d81c5aab5e5068edfb58a), Baena, Córdoba; PA calle Arquitecto Mateo Gayá 42. No fusionar automáticamente con Inmobiliaria AG Asesores de Córdoba capital: posible homonimia.

### 2 fichas existentes enriquecidas, sin duplicar
- [Linkasa Inmobiliaria](https://app.notion.com/p/41d81b1a756d81d88db0eb1025b70056), Linares: email corporativo del directorio de colegiados API Jaén `gerente@linkasa.es`, web `inmobiliarialinkasa.es`; oficina en Quevedo 2 (Páginas Amarillas).
- [Forte y Ruano S.C. / Ruano Inmobiliaria](https://app.notion.com/p/41d81b1a756d812881bff4a50b53f23e), Almería: correo y web confirmados en https://pisosenalmeria.es/contacto/ , dirección Avenida del Mediterráneo 311 y teléfono existente. No nueva sociedad si es continuación de la misma firma.

El directorio original no tiene columna propia `Dirección`; los domicilios y posibles conflictos se documentaron dentro de cada página. Se actualizaron los números de nueve localidades originales más Baena/Torredonjimeno/Écija y la corrección Lepe ↔ Isla Cristina, sin reconfigurar el esquema.

### Recuento Notion post-escritura
**4.589 fichas** / **4.587 claves únicas** / **2.802 con email** / **4.373 con teléfono**.
| Provincia | Fichas | Con email |
| --- | ---: | ---: |
| Córdoba | 508 | 276 |
| Jaén | 253 | 109 |
| Sevilla | 638 | 412 |
| Málaga | 1.712 | 1.066 |
| Granada | 439 | 296 |
| Cádiz | 528 | 334 |
| Almería | 353 | 217 |
| Huelva | 158 | 92 |
| **Total** | **4.589** | **2.802** |

**Municipios:** 325 con al menos una ficha, 459 sin ficha en fuentes consultadas, de 784 municipios de la ruta. Las 13 incorporaciones estaban en municipios que ya tenían fichas, por lo que no cambia cobertura territorial. Continuar trabajando por agencia y calidad del correo y teléfono, sin utilizar el municipio como pretexto para inflar conteos.

### Brevo
Ocho listas provinciales existentes: Córdoba #25, Jaén #26, Sevilla #27, Málaga #28, Granada #29, Cádiz #30, Almería #31, Huelva #32. **No se crearon ni duplicaron**. La lectura del conector constata **0 contactos en estas ocho listas**; el conector expone `add_contact_to_list` para contactos ya existentes, no importación de nuevos contactos. Además, la inclusión de correos extraídos de fuentes públicas para campañas no acredita el requisito legal ni el permiso de uso del proveedor. **No importar indiscriminadamente, no lanzar envíos, no cambiar estado `NO_VERIFICADA`**. No tocar NEWS-001.

### Próxima acción
Barrido sistemático por fuentes públicas/registros profesionales de las 8 provincias, cotejo por nombre+dominio+teléfono y enriquecimiento de registros ya existentes (priorizar las fichas sin correo). No afirmar haber encontrado **todas** las inmobiliarias hasta alcanzar una comparación exhaustiva de fuentes y dedup; completar dirección en notas de ficha o mediante cambio de esquema solo después de inventario/snapshot. Crear campaña después, según nueva orden del propietario.

**Resultado:** ingesta física incremental demostrada en Notion, fuentes comprobadas, sin cambios CRM/App/PROD, sin campaña y con coste adicional contratado 0 €.
