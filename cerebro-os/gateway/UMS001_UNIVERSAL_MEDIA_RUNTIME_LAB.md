# CEREBRO OS · Ruta universal UMS-001 para todos los motores REGISTRADOS · LAB

## Estado comprobado
La Fábrica FACT-001 incorpora `IMAGE.SYNTHETIC` en el scaffold. Cuando el motor se incorpora desde el repositorio de FACT mediante GitHub Actions OIDC, la identidad se inscribe en el registro firmado de UMS-001 sin configurar un Worker por motor.

Un Gateway central de FACT, `cerebro-fact001-gateway-lab-eu-20261109`, tiene ahora las operaciones privadas por Cloudflare Service Binding:
- `universalImageCapability(engineId, runtimeToken)` comprueba ACTIVE o PENDING_FACTORY_IAM
- `universalImageRequest(engineId, {request_id,prompt}, runtimeToken)` genera orden original
- `universalImageStatus(engineId, {request_id}, runtimeToken)` consulta recibo
- `universalImagePrivateJPEG(engineId, {request_id}, runtimeToken)` lee bytes privados y verifica SHA256

Todo usa un solo broker `cerebro-ums001-universal-runtime-broker-lab-eu`, que consulta FACT Vault y la productora UMS-001 firmada. Tokens protegidos en Cloudflare Worker Secrets; sin URL pública. La prueba real por cola privada de LAB quedó en `PRIVATE_ASSET_RECEIVED` y devolvió JPEG de 633388 bytes con SHA256 `8e0149691f0e7615bd0cf2a7bf8b417937b6cbfcba3dfe9c472e05dfef9e9075`.

**Importante:** este contrato habilita una ruta única por *runtime compartido*, NO significa que 177 motores tengan ya autenticación; solo hay 3 identidades de prueba ACTIVE. El Gateway central distingue `READY_AUTHENTICATED` de `PENDING_FACTORY_IAM`. Los motores que aún viven en otros runtimes (SEO WordPress, App/CRM PROD, Social otros repos, etc.) requieren registrar y conectar su **runtime** de forma segura al CEREBRO Gateway, no crear claves ni Workers por motor. Nunca abrir acceso de todos aceptando `engine_id` en JSON sin IAM.

## Evidencias, rollback y costes
- <https://github.com/carlosjmunoz78/fenix-capital-inmo-map/blob/cerebro/ums001-private-ai-image-e2e-lab-20261112/cerebro/media-studio/v2/evidence/UMS001_CEREBRO_SHARED_GATEWAY_E2E_2026-11-12.json>
- Código y backups de ambos Workers en la rama GitHub aislada y PR #46.
- Pausar sin tocar lo antiguo: `UNIVERSAL_IMAGE_RUNTIME_ENABLED=false` en Gateway FACT y `BROKER_ENABLED=false` en broker; no borrar claves/colas.
- `GATEWAY_ENABLED=false`, `ALLOW_MUTATIONS=false` y demás puertas anteriores permanecen apagadas.
- Coste adicional **no certificado** por Billing: no permitir publicar ni promocionar PROD hasta gates completos.

## Estado de promoción
- FACT GitOps automático desde motores registrados: HECHO/VERIFICADO LAB.
- FACT Cloudflare runtime compartido: HECHO/VERIFICADO LAB.
- Compatibilidad de motores existentes fuera de esos runtimes: PLANIFICADO/POR AUDITAR, con IAM por plataforma.
- CEREBRO entero autónomo en PROD: NO PROMOVIDO.
