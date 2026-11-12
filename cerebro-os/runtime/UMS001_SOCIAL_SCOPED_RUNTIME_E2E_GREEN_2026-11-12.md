# UMS-001 · SOC-001 · cierre seguro LAB (12-11-2026)

**HECHO/VERIFICADO:** la credencial independiente `CEREBRO_SOCIAL_RUNTIME_TOKEN` está instalada como Cloudflare Worker Secret. Su hash SHA-256 está registrado para el runtime `SOCIAL-LAB` en KV privado, restringido a `fenix/LAB` y motores con prefijo `SOC-` e identidad firmada FACT ACTIVE. No se ha expuesto el secreto.

SOC-001 inició desde su propio Worker una petición por el Gateway FACT y obtuvo una imagen privada real. Id `UMS001-LAB-SOC-RUNTIME-20261112-01`. JPEG 1024×1024, **756338 bytes**, SHA-256 `f67235924971b469a280ff99d82a08fed53ef576ca9a6fe0d8952abd7417dc0f`. Generación `PRIVATE_READY`, inbox FACT `PRIVATE_ASSET_RECEIVED` y Worker Social recuperó y verificó bytes + hash. Fallaron correctamente las pruebas negativas (token inválido, intento de Social acceder a SEO-001). No hubo publicación.

Flags permanentes de LAB: `SOCIAL_UNIVERSAL_IAM_ENABLED=true`, `UNIVERSAL_RUNTIME_IAM_ENABLED=true`, `SOCIAL_BRIDGE_ENABLED=true` original mantenido. `GATEWAY_ENABLED=false` y `ALLOW_MUTATIONS=false` permanecen cerrados; Worker Social y FACT sin URLs públicas. Los disparadores temporales de QA fueron retirados. Los módulos originales y secretos se conservaron durante el despliegue.

**Persistencia:** fuente exacta del Worker Social y evidencia bajo la rama `cerebro/ums001-universal-consumer-lab-20261112` de `fenix-capital-cerebro-social`. La PR #46 de UMS-001 documenta además el Gateway común y la generación.

**NO certificar:** motor Social completo publicando automáticamente, integración de Facebook/Instagram AUTOQUAL, QA visual/marca/derechos, coste de facturación real o promoción PROD. La cola previa Social continúa intacta; el nuevo camino por FACT es un API privado habilitado pero todavía no reemplaza el consumidor legacy para todos los eventos de campaña.

**WordPress STAGING:** suspendido por orden del propietario HASTA NUEVA ORDEN. Prohibido acceder o reparar.

**Rollback:** poner `SOCIAL_UNIVERSAL_IAM_ENABLED=false` en el Social Worker. Si fuera necesario, también `UNIVERSAL_RUNTIME_IAM_ENABLED=false` en Gateway FACT. No desactivar `SOCIAL_BRIDGE_ENABLED`. No revocar el secreto sin auditoría de dependencias. Cloudflare rechazó PATCH settings con 405 OAuth, por lo que el despliegue con metadata Worker PUT e inherit fue la vía oficial aplicada.
