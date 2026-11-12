# FACT-001 · Inscripción universal GitHub OIDC y primer circuito de imágenes REAL en LAB
Fecha: 12 noviembre 2026

## Éxito físico verificado
- Motor creado por el `factory.py` real y registrado en el repositorio: `FACT-OIDC-CANARY-20261112`.
- Workflow `.github/workflows/cerebro-fact-ums001-oidc-lab.yml`, disparado por modificación de `cerebro-os/engines/**/manifest.json` en rama `cerebro-engine-factory-v0`.
- Sin credenciales Cloudflare permanentes en GitHub: identidad temporal OIDC JWT firmada por GitHub, con `id-token: write`.
- Puente `cerebro-fact001-github-oidc-enroll-lab-eu` verifica RS256/JWKS, repositorio `carlosjmunoz78/capital-mapa-pro`, repo ID `1139292249`, ref y workflow exactos, `aud`, `iss`, expiración, `jti` y manifiesto real del mismo SHA. Durable Object SQLite previene repetición.
- El Worker utiliza un Service Binding y un secreto cifrado exclusivo para hablar con el provisionador ya existente; los secretos no se escriben en GitHub ni en la conversación.
- **Evidencia del trabajo REAL**: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43255172953, intento final exitoso. El runner registró `FACT-OIDC-CANARY-20261112 state=ACTIVE signed_probe=REGISTERED_QA_PENDING`.
- En Cloudflare Vault: registro `ACTIVE`, `encrypted_private_key=true`, `activated_at=2026-11-12T16:09:30.946Z`.
- **Evidencia E2E del segundo workflow real**: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43256289803; el runner emitió una solicitud firmada privada `UMS001-LAB-GITHUB-OIDC-IMAGE-20261112-01` y recibió `ACCEPTED`.
- Productora `cerebro-ums001-registered-image-executor-lab-eu` emitió `PRIVATE_READY`: imagen JPEG original 1024×1024 de 692999 bytes; SHA256 `9b84d21fe306c2dcecf414badb3799715a29c4492562188a12bc5d9e7e7cb589`. El receptor compartido FACT registró `PRIVATE_ASSET_RECEIVED`, mismo SHA256 y tamaño. Sin publicación ni entrega a sistemas ajenos.

## Persistencia y modos de ejecución
- Cada futuro motor incorporado por FACT-001 al branch controlado y con `manifest.json` válido hereda el **mismo** flujo de inscripción, sin Worker ni secreto por motor. Fuera de la rama aprobada, company_id fenix y LAB, se deniega por defecto.
- Un motor debe **solicitar** imágenes mediante el Gateway y la interfaz autenticada; no se generan imágenes por el mero hecho de existir. La llamada adicional de prueba se ejecutó una sola vez y fue retirada del `main()` del workflow para evitar generación de prueba recurrente.
- El método de prueba `request_image_lab_canary()` permanece como helper de laboratorio, restringido al motor de ensayo; el Gateway compartido tiene el método de solicitud de imágenes para cualquier motor debidamente registrado, con IAM de origen.
- Las modificaciones no migran de forma invasiva motores ya existentes; la adopción en runtime fuera del flujo GitHub requiere que sus emisores invoquen el Gateway común con credenciales/firmas verificables.
- Multiempresa adicional, publicación, QA visual y de marca, licencias y costes facturados siguen sin certificar. La quota de Workers AI no reemplaza un límite transaccional.

## Troubleshooting y correcciones
- Error inicial HTTP 403 de Browser Integrity Check en `workers.dev` al usar el User-Agent predeterminado de Python. Corregido en el cliente HTTP sin desactivar Cloudflare BIC.
- Cloudflare Worker rechazó `redirect:'error'`; cambiado a `redirect:'manual'`, que permite rechazar respuestas 3xx sin seguirlas.
- Sólo se imprimen códigos de error sanitizados; nunca OIDC JWT, tokens, claves ni payloads sensibles.

## Seguridad y rollback
- Desactivar `OIDC_BRIDGE_ENABLED` en `cerebro-fact001-github-oidc-enroll-lab-eu`, luego deshabilitar workers.dev si hace falta aislar HTTP. Los demás Workers FACT/UMS no tienen subdominios públicos.
- Para parar generación: desactivar `REGISTERED_IMAGE_ENABLED` del Gateway y `ENABLED` del ejecutor universal; el registro histórico y sus pruebas permanecerán.
- Código y snapshot en PR #46: https://github.com/carlosjmunoz78/fenix-capital-inmo-map/pull/46
- No se modificaron main, PROD, App, CRM, DNS, WordPress, Buffer ni Trading.
