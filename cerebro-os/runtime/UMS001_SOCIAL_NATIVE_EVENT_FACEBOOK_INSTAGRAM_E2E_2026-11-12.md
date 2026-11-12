# UMS-001 / SOCIAL native V2 · Cierre de generación automática por eventos · 12-11-2026

## HECHO y VERIFICADO en LAB
- Nuevo consumidor de eventos de briefs aprobados `SOCIAL_CREATIVE_APPROVED_V2`, independiente de la cola Social original. Una sola cola EU y un único Worker compartido `cerebro-ums001-social-creative-bridge-lab-eu`.
- La función de cola genera sin intervención adicional, programa su propia comprobación diferida y verifica el JPEG privado mediante FACT Gateway/IAM SOC-001 y SHA256, guardando `PRIVATE_ASSET_RECEIVED`.
- Ejecución real por dos **eventos administrativos de campaña ficticia LAB**, uno para Facebook (`SOCIAL-V2-FB-LAB-20261112-01`; 648993 bytes; SHA `c291a90602ecffa08ac97bdc81999702a61dccad2e7fc5807c51cff841495f45`), otro para Instagram (`SOCIAL-V2-IG-LAB-20261112-01`; 778539 bytes; SHA `89251f3849b31f2146c5f2b4ead48986a317352b9767fafe8b8be6d09cf5a573`).
- Prueba adversarial: evento con `publish_requested=true` rechazado con `SOC_V2_APPROVAL_SCOPE`, sin imagen ni incremento del contador. Dos solicitudes aceptadas, cupo diario V2 LAB=2 (contador KV no es techo económico global).
- El Worker tiene ahora un RPC privado `SocialUniversalMediaRuntime.submitApprovedCreative(item)` para que un editor real autenticado pueda enviar futuros briefs. **No se ha conectado ni probado un emisor editorial real:** los dos eventos fueron insertados por API administrativa, no por un calendario autónomo.
- Ni Buffer ni Meta reciben órdenes: dos imágenes privadas `QA_PENDING` (brand/visual/derechos/formato/claims sin aprobar). Los dos JPEG son 1024x1024; las fichas finales de Facebook requieren 1080x1080 e Instagram 1080x1350. Antes de publicar requieren transformación y revisión visual.
- El pipeline anterior Social `SOCIAL_CONTENT_REQUESTED` conserva su consumidor original y `SOCIAL_BRIDGE_ENABLED=true`.
- GitHub de Social: workflow falló en los runs `43276527192` y `43276729084`; el servicio no entrega logs/steps. No afirmar CI verde. Suite local combinada de consumidor antiguo + contratos V2 pasó **12/12**; Worker FB Autoqual pasó **11/11** en local.

## Facebook Autoqual independiente y apagado
- Worker aislado `cerebro-facebook-autoqual-lab` desplegado por primera vez usando exclusivamente `cloudflare/facebook-autoqual-lab/src/worker.mjs` del repositorio Social de LAB.
- D1 europea aislada `cerebro-facebook-autoqual-lab`, UUID `e8fe801d-4b01-4e34-ac12-26014b79adc1`, tabla D1 de estado inicializada a `mode=OFF`, 0 casos sellados, 0 llamadas, cola vacía. Baseline bookmark `00000003-00000000-00005121-dc0dd60bea982bdb818d7542f7b25b54` anterior a la migración exclusiva `0001_init_lab.sql`. No se modificó D1 Instagram ni otra.
- `AUTOQUAL_ENABLED=false`, `GROQ_ENABLED=false`, `COST_CEILING_EUR=0`; 0 crons, 0 URLs públicas, 0 publicaciones y 0 formación semántica.
- Instagram Autoqual continúa OFF; ningún cambio en su Worker.

## Restricciones aún necesarias para publicación autónoma
Acreditar origen editorial con identidad, transformar salida para cada red, verificar derechos, marca, legalidad de reclamaciones financieras y accesibilidad, firmar la entrega UMS-001, validar permisos Meta/Buffer de cada canal, cron/cadencia T-48, deduplicación y rollback ensayado. No habilitar el publicador hasta que pasen TODOS los gates. Coste facturado Cloudflare no verificado.

WordPress STAGING está suspendido hasta orden expresa del propietario; no acceder, reparar ni probar. PROD, App, CRM, DNS y main permanecen intactos.

## Reversión
1. `SOCIAL_NATIVE_V2_ENABLED=false` en el único Worker Social; preservar `SOCIAL_UNIVERSAL_IAM_ENABLED=true` y `SOCIAL_BRIDGE_ENABLED=true`.
2. Archivar cola V2 y recibos sin borrarlos, restaurar `cloudflare/ums001-native-social-lab/worker.before-editorial-rpc.v2.mjs` si hay regresión OLD vs NEW.
3. FB Autoqual queda OFF; no quitar D1 ni tocar Instagram.
4. Retener snapshots y evidencias. Ni generación de imagen significa autorización a publicación ni D1 creada significa entrenamiento completado.
