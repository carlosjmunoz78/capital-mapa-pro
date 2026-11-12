# UMS-001 · Evidencia ampliación SEO/Social · LAB · 12-11-2026

## SEO-001: HECHO/VERIFICADO (ruta FACT GitOps)
- FACT-001 creó el manifiesto de identidad `cerebro-os/engines/SEO-001/manifest.json`, con `status=DEFINED_NOT_BUILT` para no declarar el motor SEO instalado.
- GitHub OIDC enrollment: SUCCESS en https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43269076272.
- Cloudflare Vault: SEO-001 ACTIVE, clave privada cifrada, firma aceptada REGISTERED_QA_PENDING.
- Petición de prueba de imagen desde FACT GitOps: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43269333725 (SUCCESS), artefacto privado https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43269333725/artifacts/13968180433 (expira 13-11-2026).
- FACT UMS registro: `UMS001-LAB-SEO001-GITOPS-20261112-01`, JPEG 1024×1024, 389149 bytes, SHA256 `4cc7078e5f4bbc0e6af72bc9e740b73acc267be28c4928562a63d0f14c734e43`.
- Generación `PRIVATE_READY` y entrega `PRIVATE_ASSET_RECEIVED` coinciden por request_id, bytes y SHA256. QA técnico PASS. Marca/visual PENDING. Publicación false.
- **No es la conexión nativa WordPress ni SEO PROD**: STAGING WordPress MCP devolvió fallo de servicio al consultar herramientas de lectura, por tanto no se modificó ni pudo certificar runtime de SEO WordPress.

## Social: PARCIAL seguro
- Código del Worker `cerebro-ums001-social-creative-bridge-lab-eu` ampliado aditivamente: `SocialUniversalMediaRuntime.capability/requestPrivateImage/privateReceipt/privateJPEG` acepta ahora `engineId` SOC-* opcional, sin Worker por motor, manteniendo compatibilidad con las llamadas a SOC-001 previas.
- La ruta antigua SOCIAL_CONTENT_REQUESTED permanece intacta y activa.
- La ruta nueva sigue `SOCIAL_UNIVERSAL_IAM_ENABLED=false`, la política de FACT `UNIVERSAL_RUNTIME_IAM_ENABLED=false`; las dos están apagadas hasta que Cloudflare permita instalar y verificar el token por runtime. El token no se ha mostrado ni eludido.
- No se ha declarado Social universal LIVE ni probado E2E a través de la ruta nueva; sí hay evidencia anterior de su ruta Social legacy.
- Instagram AUTOQUAL LAB continúa OFF; no activar publicaciones ni usar Buffer.

## Persistencia y recuperación
- Código y snapshots de Social en la rama LAB de fenix-capital-inmo-map bajo `cerebro/media-studio/v2/runtime/ums001-cloudflare-lab/backups/`.
- Toda esta documentación en `capital-mapa-pro` rama `cerebro-engine-factory-v0`. No fusionar a main, no tocar App/CRM, Supabase PROD, DNS, WordPress ni Trading.
- 5 identidades de pruebas ahora figuran ACTIVE en LAB (FACT-MEDIA-CANARY-001, FACT-OIDC-CANARY-20261112, FACT-OIDC-LAB-E2E-001, SOC-001, SEO-001). 177 IDs en el catálogo NO significan 177 motores con runtime activo.
- Billing real Cloudflare NO_VERIFICADO.
