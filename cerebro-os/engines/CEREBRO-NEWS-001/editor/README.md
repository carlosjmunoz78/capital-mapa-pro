# NEWS-001 · Motor editorial ORIGINAL de CEREBRO (RESTAURADO)

## Estado
Código recuperado íntegro desde el paquete creado el 17 de noviembre de 2026 por la propia Factory. Esta carpeta NO usa la versión reducida ni inventa otra maqueta.
**No está conectado a envíos:** `send_enabled=false`, `approved=false`, ningún permiso de creación de campañas ni listado de usuarios.

## Contrato visual inmutable
Diez módulos por audiencia, 13 enlaces, logotipo original PNG, héroe B2B/B2C JPG, naranja #FF5F00, fondo marfil/claro, dos audiencias diferenciadas, CTA, redes, y baja Brevo. No permitir 0 imágenes ni 3 módulos. Imágenes guardadas en GitHub codificadas `.b64` para asegurar exactitud; el workflow las reconstruye y valida SHA-256 antes de renderizar. Nunca sustituir por fotos AI con QA rechazada.

## Ejecución reproducible LAB sin IA de pago
1. Instalar beautifulsoup4 4.12.3 (dependencia opensource, coste de licencia 0).
2. `for f in assets/*.b64; do base64 -d "$f" > "${f%.b64}"; done` y verificar SHA-256.
3. `python3 ejecutar_prueba_semanal.py --date 2026-11-18`; genera `out/NEWS_FENIX_b2b_...html` y `out/NEWS_FENIX_b2c_...html`, más `RESULTADO_PRUEBA.json`.
4. `python3 tests/test_cerebro_reproduces_full_design.py` y las pruebas previas.

Workflow: `.github/workflows/news001-cerebro-generator-lab.yml`, se ejecuta automáticamente en la rama LAB cuando cambian archivos del motor, no en main. Los archivos regenerados son artefactos privados de CI, no campañas de Brevo.

## Freshness: PRECAUCIÓN
El registro `news_observer_verified.json` reproduce un snapshot de fuentes declarado verificado por el paquete original del 17/11. El procedimiento semanal rechaza fuentes ausentes o caducadas; no presupone noticias nuevas ni consulta internet. Nueva ejecución futura requiere que un motor de Research entregue fuentes contrastadas y actualice el registro. Para otras fechas no alterar cifras ni crear falsas noticias.

## Entregabilidad: HOLD
Antes de habilitar publicación: verificar documentos oficiales actuales, originalidad, copyright y QA visual, URLs públicas HTTPS del logo/héroes y enlaces, contenido legal, consentimiento web/social, Salinas excluida, límites Brevo, bajas, DOI y pruebas E2E a buzón autorizado. Los originales son candidatos visuales; no producción.

## Reglas
Preservar App/CRM/WordPress/Supabase existentes, no alterar main ni sucursales. Cero suscripciones adicionales. No prometer autonomía PROD sin prueba de envío segura.
