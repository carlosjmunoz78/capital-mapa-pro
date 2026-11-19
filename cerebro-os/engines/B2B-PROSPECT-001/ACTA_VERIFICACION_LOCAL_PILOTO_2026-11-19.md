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
