# CEREBRO OS · UMS001 IMÁGENES UNIVERSALES · ESTADO FÍSICO Y CONTINUIDAD

Fecha 12-11-2026. Objetivo: todo motor registrado puede solicitar y recibir imágenes mediante un único Gateway y un cliente compartido, sin integrar cada motor por separado.

## Estructura que permanece
- FACT-001 inscribe motores nuevos en el registro firmado usando GitHub OIDC efímero sin guardar API keys en GitHub.
- FACT Cloudflare LAB central usa `universalImageCapability/Request/Status/PrivateJPEG`. Su broker compartido UMS-001 ha generado un JPEG real y el Gateway ha recuperado los bytes, verificado SHA256.
- Cliente multi-runtime `cerebro-os/runtime/ums001_universal_media_client.mjs`: una sola conexión por **runtime**, rutas de petición/estado/descarga y verificación SHA256. **8/8 pruebas Node locales PASS** el 12-11-2026. Se ha añadido workflow CI LAB de regresión; no afirmar que ya pasó GitHub Actions sin un run SUCCESS.
- No se han alterado App, CRM, Supabase PROD, SEO/WordPress, Buffer, trading, DNS ni main; no hay publicación automática.
- **Social** conserva su cola de generación anterior. Nuevo Service Binding a FACT y clase `SocialUniversalMediaRuntime` instalados **en paralelo**, con flags OFF. FACT Gateway tiene IAM genérico por runtime para evitar impersonación: compara SHA256 de token, runtime_id, compañía, LAB, prefijo de motor SOC- y clave ACTIVE en FACT Vault. El nuevo token SOC no pudo instalarse porque el control de seguridad de la conexión bloqueó el intento. No repetirlo a través de una vía alternativa. Social no está aún verde por la vía nueva.

## Conexión nueva definitiva: una vez por runtime
Al activar un **runtime físico** (no un motor lógico): validar identidad firmada y empresa, inscribir token del runtime con un método permitido en el Vault, añadir un Service Binding al FACT Gateway, consumir el SDK común, comprobar que los motores nuevos de su prefijo se aprovisionan automáticamente por FACT OIDC, verificar rechazos entre runtimes, E2E con JPEG privado/SHA256, visual/brand QA y gates de coste/rollback antes de migrar o promocionar. No otorgar a un runtime el token global de FACT para evitar suplantación.

## Estados sin falsear
- LAB FACT GitOps y FACT Cloudflare: HECHO / VERIFICADO.
- LAB Social existente: EXISTENTE / CONSERVADO; Social Universal nuevo: PARCIAL, token bloqueado, OFF.
- Instagram AUTOQUAL LAB: OFF, Social Facebook: POR AUDITAR.
- SEO WordPress, App/CRM PROD y demás runtimes: POR AUDITAR y SIN PROMOCIÓN.
- 177 identificadores del catálogo NO implican 177 motores desplegados. No afirmar autonomía universal PROD.
- Billing Cloudflare sin permiso de lectura: costes facturados NO VERIFICADOS.
- Los recursos LAB nuevos quedan persistidos en Cloudflare, el código versionado en ramas aisladas, no en main. No confundir despliegue LAB con producción.

## Rollback
Primero desactivar `SOCIAL_UNIVERSAL_IAM_ENABLED` y `UNIVERSAL_RUNTIME_IAM_ENABLED` del Gateway FACT, mantener `SOCIAL_BRIDGE_ENABLED=true` para la conexión anterior. Si fuera necesario restaurar los snapshots en la rama `cerebro/ums001-private-ai-image-e2e-lab-20261112` con tests OLD vs NEW. No borrar recursos ni secretos existentes sin inventario.
