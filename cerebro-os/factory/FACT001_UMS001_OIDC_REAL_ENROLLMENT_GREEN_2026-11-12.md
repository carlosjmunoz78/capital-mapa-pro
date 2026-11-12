# FACT-001 → UMS-001 · CIERRE del alta automática GitHub OIDC · LAB · 2026-11-12

## HECHO / EVIDENCIA FÍSICA
Se ha completado por primera vez la inscripción universal de un motor nuevo de FACT-001 desde una ejecución **real** de GitHub Actions, sin API token Cloudflare ni firma HMAC persistente en GitHub:
- Workflow existente: `.github/workflows/cerebro-fact-ums001-oidc-lab.yml`, en rama `cerebro-engine-factory-v0`. Detecta el nuevo manifiesto bajo `cerebro-os/engines/**/manifest.json`; `permissions: contents: read, id-token: write` solo en su job.
- Emisor: `cerebro-os/factory/oidc_enroll_changed_engines.py`, toma JWT OIDC efímero de GitHub y lo envía al Worker OIDC existente `cerebro-fact001-github-oidc-enroll-lab-eu`.
- El Worker comprueba firma RS256 contra JWKS de GitHub, audience, `repository`, **repository_id=1139292249**, rama, `workflow_ref`, SHA del commit y `event_name=push`; bloquea reutilización con Durable Object `OIDC_REPLAY`; consulta manifiesto real en GitHub por SHA; requiere capacidad `IMAGE.SYNTHETIC` y políticas LAB.
- Envía el alta al provisionador privado `cerebro-fact001-ums001-issuer-provisioner-lab-eu`, con credencial protegida por Worker Secret. El provisionador genera clave Ed25519 cifrada y registra la pública ante el Gateway UMS-001.
- Motor creado por fábrica Python y guardado en rama LAB: `FACT-OIDC-LAB-E2E-001`.
- **Ejecutado y terminado VERDE:** https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/43255769366 (job `131313426383`, conclusión SUCCESS).
- Línea de log verificada: `FACT-001 -> UMS-001 LAB: FACT-OIDC-LAB-E2E-001 state=ACTIVE signed_probe=REGISTERED_QA_PENDING`.
- Cloudflare Vault comprobado por lectura: `state=ACTIVE`, `engine_id=FACT-OIDC-LAB-E2E-001`, `encrypted_private_key=true`, `signing_test=REGISTERED_QA_PENDING`; activación `2026-11-12T16:10:41.850Z`.
- La incidencia de ejecuciones anteriores era `INVALID_REDIRECT_VALUE` en Workers fetch; la ruta en uso se ha corregido a `redirect:'manual'`, sin relajar identidad ni permisos. Hubo 5 runs previos fallidos; no se han dado por verdes.
- No se publicaron redes ni se realizaron generación/pago en esta alta. GitHub Secrets permanentes nuevos: **ninguno**.

## Flujo de motores nuevos
`FACT-001 genera scaffold en repo LAB → commit en rama factory → workflow push detecta manifiesto → GitHub OIDC temporal → Gateway Cloudflare protegido → registro de clave → ACTIVE`.
Sin Worker por motor y sin conexión manual nueva cada vez. La plantilla inicial guarda `PENDING_FACTORY_IAM_TRANSPORT` al generarse localmente; **el registro dinámico de Cloudflare es la fuente definitiva**. No confundir ese artefacto previo al CI con estado definitivo del motor.

## LO QUE NO ESTÁ RESUELTO
- Esta prueba verifica alta e identidad firmada, NO generación y devolución de imagen iniciada autónomamente por el runtime propio de este motor nuevo. El E2E técnico de imagen desde un motor previamente registrado por vía privada se verificó antes: `FACT-MEDIA-CANARY-001` → JPEG 1024² → `PRIVATE_ASSET_RECEIVED`, SHA coincidente.
- El SDK o control-plane compartido para que **todos los motores existentes** emitan solicitudes y recojan imágenes sin intervención manual sigue pendiente de integración; una identidad registrada no equivale a permiso de publicación ni a una petición autónoma.
- El alta automática de motores nuevos requiere que se generen/registren manifiestos en la rama vigilada. Otros repos, ramas, empresas o motores externos no están aprobados automáticamente. Multiempresa fuera de `fenix` sigue deshabilitada.
- QA visual/comercial, marcas, coste facturado, publicación y promoción a PROD requieren gates independientes.

## Seguridad / rollback
- No modificar App, CRM, Supabase PROD, DNS, WordPress, Social ni Trading.
- GitHub `contents:read` en el job, `id-token:write` efímero; no instalar claves permanentes en Secrets.
- Worker OIDC: apagar `OIDC_BRIDGE_ENABLED` o su subdominio para detener altas externas. Provisionador sigue protegido por secreto privado; no abrir `REGISTRATION_WINDOW_ENABLED`.
- Código/acciones se conservan en rama `cerebro-engine-factory-v0` sin fusionar a main.
