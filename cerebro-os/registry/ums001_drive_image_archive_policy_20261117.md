# CEREBRO OS · UMS-001 · ARCHIVO DE TODAS LAS IMÁGENES · DIRECTIVA 2026-11-17

**Estado:** DIRECTIVA_REGISTRADA · ARCHIVO_4_ORIGINALES_DRIVE_VERIFICADO · AUTO_SINCRONIZACIÓN_PROGRAMADA_NO_AÚN_CERTIFICADA.
**Ámbito:** imágenes generadas a través de la Productora UMS-001, para cualquier motor y empresa registrados en FACT-001. No afirmar cobertura de generadores no conectados a UMS-001.

## Contrato vinculante de nuevos activos
1. Siempre conservar el fichero ORIGINAL intacto, sin compresión destructiva ni sobreescritura. Resguardar copia verificable en Google Drive bajo `CEREBRO / UMS-001 · ALMACÉN AUDIOVISUAL CEREBRO / 00 · RESGUARDO COMPLETO ORIGINALES IMÁGENES / NUEVOS ORIGINALES · UMS-001 · MULTIEMPRESA / <company_id> · <engine_id>`. Guardar JPEG, PNG o WebP de forma INDIVIDUAL, y conservar lote/ZIP y recibos cuando existan.
2. Identificar: company_id, engine_id, environment, version, request_id, fecha, motor/productora, fuente/prompt autorizado, licencia/derechos, dimensiones, formato, SHA256, coste si verificable, estado visual/brand/tribunal y Drive file_id. Para contenidos de otras empresas, no mezclar archivos ni reutilizar entre company_id sin autorización.
3. Validar SHA256 y tamaño antes y después de la transferencia. Duplicados = misma huella exacta SHA256 o request_id/artefacto previamente archivado; no sobrescribir ni duplicar.
4. Marcar las imágenes `REUSABLE_AFTER_VISUAL_BRAND_RIGHTS_QA`. La copia privada de Drive NO es una URL pública de WordPress/Brevo/Meta. Cualquier reutilización debe derivar un archivo público aprobado, con derechos, metadatos, ALT, formato adaptado y trazabilidad.
5. No modificar piezas ya publicadas, landing, CRM, App, DNS, bases de datos ni automatizaciones vigentes. Coste adicional 0 €, no añadir suscripciones. Estado `ARCHIVE_FAILED` debe alertarse cuando falte conector, capacidad, recibo o pruebas.

## Evidencia física del 17-11-2026
- Reutilizado almacenamiento existente UMS-001, NO creado otro almacenamiento raíz. Se abrió subdirectorio `NUEVOS ORIGINALES · UMS-001 · MULTIEMPRESA` y su subcarpeta `fenix · CEREBRO-NEWS-001 · newsletters`, permisos privados.
- GitHub run real UMS001 GitOps: `44147612208`, artifact `14356454034`, SHA de commit `6b9c6b326a277f4da3b92eaba821d3941480fd2a`.
- 2 imágenes nuevas: `UMS001-LAB-NEWS001-B2C-20261117-02` SHA256 `6b4b1596ec87efd30f4d7ac677e19514a10f6896b22587dddcec06a23c8c2791` (609127 bytes), `UMS001-LAB-NEWS001-B2B-20261117-02` SHA256 `c227a0723d89a2ff8292d709bd171aa617a8cfb27dbeb64ea508df23c87dfc18` (506693 bytes).
- 2 imágenes anteriores rescatadas de archivo existente del 17-11-2026: `UMS001-LAB-NEWS001-B2C-20261117-01` SHA256 `d2fc3c59b906ac109ac93571813302d20583b039d18909c3e553157f0d640467` (689760 bytes), `UMS001-LAB-NEWS001-B2B-20261117-01` SHA256 `417df9bd60f75a64672485cbe28faf11327d01d02f81be885fde99520e822a6b` (539633 bytes).
- Los cuatro originales verificados `image/jpeg, 1024x1024` individualmente y por tamaño de archivo en Drive; archivo ZIP adicional de las dos imágenes nuevas y recibos también preservado. Visual QA y brand QA siguen PENDING: NO aprobar publicación.
- Automatización ChatGPT separada `UMS-001 · Guardar imágenes en Drive`, cada cuatro horas: inspeccionar nuevos artefactos UMS, descargar, extraer, SHA256, deduplicar, archivar, alertar sobre errores. Estado `SCHEDULED_FIRST_FUTURE_RUN_PENDING`: todavía no certificar la sincronización futura hasta observar al menos una ejecución correcta.

## Compatibilidad, coste y reversión
No se cambia el runtime UMS, GitHub Actions existente, Cloudflare, WordPress, Brevo, App/CRM ni recursos externos; solo Drive y documentación de la regla. Sin credenciales nuevas ni nuevas suscripciones. Reversión = pausar el archivado futuro; nunca borrar originales ya resguardados.

## Próximos gates para autonomía plena
Cierre de observabilidad de la tarea tras primer run de seguimiento, cubrir todos los workflows de generación registrados (no solo el GitOps NEWS-001), asegurar idempotencia histórica, y confirmar que no haya assets generados que queden sin respaldo antes de expirar sus artifacts.
