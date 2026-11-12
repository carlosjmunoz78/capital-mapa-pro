# CEREBRO UMS-001 · Cierre de pruebas de Social y WordPress STAGING HOLD · LAB

Fecha: 2026-11-12. WordPress STAGING se encuentra suspendido por orden expresa del propietario, **no tocarlo ni monitorizarlo hasta nueva orden**. No es rojo de proyecto. El seguimiento automático UMS-001 se actualizó para respetarlo.

## Verificación Social por rutas actuales

1. **Legacy Social Instagram**, orden administrativa de prueba `UMS001-LAB-SOC-LEGACY-20261112-VERIFIED01`: motor de generación recibió y procesó la orden LAB de forma automática, `PRIVATE_READY` y acuse `PRIVATE_ASSET_RECEIVED`, JPEG 1024×1024 de 728054 bytes, SHA256 `d6b8cc41f078a864ca5070996614cf78c49222a031e8986bfdf8f211e15b078a`. Sin publicación. La orden fue introducida manualmente como administrador en cola privada, NO emitida desde Instagram real.
2. **Legacy Social Facebook**, ensayo de cola administrativa `UMS001-LAB-SOC-FB-LEGACY-20261112-VERIFIED01`: `PRIVATE_READY`/`PRIVATE_ASSET_RECEIVED`, JPEG de 594994 bytes, SHA256 `17a1f4a023df0a025bd023ea41ee030b7075aa39af769b163ef9b4a6cb041f9b`. Sin publicación. También es prueba administrativa, no emisor Facebook autónomo.
3. **Seguridad**: intento deliberado de enviar evento Social con `publish_requested=true` fue rechazado en `UMS001_SOCIAL_SPEND_PUBLISH`, no creó recibo ni lanzó publicación.
4. **SOC-001 GitOps** en workflow universal firmado por GitHub OIDC, usando el mismo cliente que FACT/SEO: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43272216971 → SUCCESS, imagen privada de 625712 bytes, SHA256 `08d61fb2ac08d66893327149db50d15413f8be57733c0e124a0afda83d71e052`, acuse final `PRIVATE_ASSET_RECEIVED`. Archivo privado: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43272216971/artifacts/13968038126. Es una petición originada por workflow FACT autenticado como SOC-001, **no un evento autónomo desde la lógica Social nativa**.
5. SDK común de runtimes: **12/12 pruebas** en Node local y en GitHub CI https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43271758110, con comprobaciones de identidad, contenido, SHA, publicación y prohibición de reactivar STAGING.

## Lo que permanece en HOLD (no falsear VERDE)
- Social Cloudflare runtime nuevo: `SOCIAL_UNIVERSAL_IAM_ENABLED=false`; FACT Gateway `UNIVERSAL_RUNTIME_IAM_ENABLED=false` hasta disponer de credencial scoped del runtime Social instalada por vía permitida y probar petición desde emisor real. La conexión Social legacy existente no debe borrarse.
- Cola `cerebro-ums001-social-creative-event-lab-eu` tenía consumidor Social, pero lista de **producers vacía** en la consulta Cloudflare, por lo que todavía no hay evidencia de emisión autónoma por un Worker Social real. Las pruebas de cola administrativas no solucionan ese origen.
- Instagram y Facebook AUTOQUAL son motores diferentes de la mera generación de imágenes; su publicación sigue desactivada, como estaba previsto.
- WordPress STAGING excluido hasta orden nueva. WordPress PROD, App, CRM, Trading, DNS, main, y publicaciones intactos. Coste facturado no certificado.
