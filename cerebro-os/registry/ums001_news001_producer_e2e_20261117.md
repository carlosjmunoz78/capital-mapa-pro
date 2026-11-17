# UMS-001 · Productora universal · NEWS-001 · Prueba real de acceso

**Fecha:** 17/11/2026 · **Entorno:** LAB · **Empresa de CEREBRO UMS:** `fenix` (equivalente técnico del ámbito Fénix Capital; no usar como alias global de otra empresa) · **Motor:** `CEREBRO-NEWS-001`.

## Autorización del propietario
Todo motor registrado de CEREBRO podrá solicitar capacidades de la Productora mediante FACT-001 + Gateway UMS-001 con identidad firmada y permisos; no implica acceso público, gasto de IA, publicación o acceso a datos de otros motores. Registrar un motor nuevo mediante manifest `cerebro-os/engines/<ENGINE_ID>/manifest.json`, validado por `cerebro-fact-ums001-oidc-lab.yml`. Prohibido crear Workers individuales innecesarios o cambiar consumidores legacy. Implementado aquí solo `IMAGE.SYNTHETIC`, con privilegios mínimos, publicación OFF y presupuesto adicional 0 EUR por solicitud.

## Ejecución física
**Registro manifest:** commit `9d9f9725362273a34f759231b7c59240407f3d7d`, rama `cerebro-engine-factory-v0`. Comprobación Cloudflare de `ISSUER_VAULT` `meta/fact001-ums001-issuer/v1/engines/fenix/LAB/CEREBRO-NEWS-001`: state **ACTIVE**, key_id y clave privada cifrada presentes. signing_test `REGISTERED_QA_PENDING`: no afirmar QA visual/brand completo.

**Solicitudes reales a Productora:** commit `5e4782a4c27bf0d2e0901aa45794b7f366795ac3` (dos JSON inmutables), GitHub Actions [run 44134737046](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/44134737046) **SUCCESS** con pasos: schema/security unit, fetch original images SHA256 via OIDC, artifact. Archivo de GitHub `14351891748` — descarga del artefacto caduca; [copia permanente privada en Google Drive](https://drive.google.com/file/d/1zuOuYMk16-7AmLmWK2Cpum-Zo9Z9Tliy/view).

- **Particulares** `UMS001-LAB-NEWS001-B2C-20261117-01`: `PRIVATE_ASSET_RECEIVED`, JPEG 1024², 689760 bytes, SHA256 `d2fc3c59b906ac109ac93571813302d20583b039d18909c3e553157f0d640467`.
- **Inmobiliarias** `UMS001-LAB-NEWS001-B2B-20261117-01`: `PRIVATE_ASSET_RECEIVED`, JPEG 1024², 539633 bytes, SHA256 `417df9bd60f75a64672485cbe28faf11327d01d02f81be885fde99520e822a6b`.
- En ambos: `technical_qa=PASS`, `visual_qa=PENDING`, `brand_qa=PENDING`, `publish_authorized=false`.
- Se verificaron físicamente los dos bytes extraídos de artefacto GitHub con sha256 y formato JPEG 1024x1024.

## Noticias y newsletters
Se recompusieron exactamente **dos** ediciones de laboratorio conservando **10 bloques** por segmento, titulares originales, imágenes nuevas de la Productora, noticia del euríbor y tipos BCE y CTA en Fénix; PDF 1 página larga y **13 enlaces** por edición. Capturas HTML en 800px y 390px sin desbordamiento, las 2 imágenes de cada correo cargan. [ZIP de las dos newsletters + PDFs + capturas + imágenes + QA](sandbox:/mnt/data/CEREBRO_NEWS001_DOS_NEWSLETTERS_CON_PRODUCTORA_REAL_20261117.zip) (enlace del entorno de ejecución, no referencia permanente GitHub; SHA256 `fee520c399099d80e7d7b620b5cbef69a002b6706d4c0cade85794397c05f246`).

**Advertencias:** El texto procede del **fallback determinista** CEREBRO con fuentes, no de una redacción DeepSeek exitosa (pruebas DeepSeek aún dan 503). Las fotos se revisaron visualmente, pero requieren aprobación estética y de marca; son recursos LAB de Workers AI, no se les debe atribuir el mismo acabado del render original de ChatGPT. El HTML de vista previa utiliza imágenes privadas embebidas y **no está listo para Brevo**, que necesita URLs HTTPS públicas y estables de assets aprobados. No enviar nada sin legal/DOI/bajas y QA de correo. La generación de activos no demuestra scheduling recurrente ni conexión automática nativa NEWS → Productora: las peticiones fueron GitOps iniciadas de forma explícita, no emitidas por un scheduler newsletter.

## Rollback y continuidad
Sin cambios en App, CRM, WordPress, Brevo, DNS, Supabase, Social, SEO, runtimes UMS compartidos ni main. No URLs públicas nuevas, ni cron, ni publicaciones; solo manifest de motor y dos media-requests en rama LAB. El siguiente motor se inscribe por FACT-OIDC bajo políticas firmadas, no por credencial universal compartida. La inscripción puede suspenderse sin afectar otros motores.
