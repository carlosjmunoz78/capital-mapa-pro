# CEREBRO UMS-001 · Visión automática · RUNBOOK DE CONTINUIDAD 17-11-2026

## MISIÓN
Impedir que fotos incoherentes o con texto falso lleguen a newsletters, WordPress o redes; conservar originales y automatizar el control mediante inspección visual verificable sin gastos nuevos.

## HECHO FÍSICO
1. **Rechazos conocidos:** B2C foto `6b4b1596...` (anatomía y letras), B2B foto `c227a072...` (texto artificial), ambas en `cerebro-os/quality/ums001_visual_rejections.json`. En Google Drive cuatro JPEG originales privados, dos renombrados `RECHAZADA_QA...NO_USAR` y otros dos pendientes. Sin borrado.
2. **Fail-closed GitOps:** `cerebro-os/factory/ums001_visual_qa_gate.py` rechaza hashes conocidos; para activos desconocidos sin informe independiente firmado: `QA_HOLD`, `reuse_allowed=false`, `publish_authorized=false`. Esto no supone que ya exista inspector con visión en PROD.
3. **Inspector de IA implementado en código:** `cerebro-os/quality/ums001_visual_ai_auditor.mjs`; llama a `@cf/meta/llama-3.2-11b-vision-instruct` solo con `VISION_QA_ENABLED=true`, `VISION_QA_COST_VERIFIED=true` y binding AI. Verifica anatomía, extremidades, manos, caras, fake text, geometría y correspondencia con el brief. Rechaza defectos manifiestos, HOLD si hay dudas, modelo no disponible o respuesta inválida. Una respuesta limpia de un único modelo queda `QA_CANDIDATE_UNCALIBRATED`, **no apta todavía para publicación ni reutilización autónoma**.
4. **Pruebas CI reales:** run GitHub [44154135550](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/44154135550) 16 tests Node PASS. Adaptador `cerebro-os/factory/universal_media_gitops_lab.py`: ruta optativa `/v1/factory/image-review` por OIDC GitHub con validación de empresa/motor/request/hash; habilitación `UMS001_VISION_QA_API_ENABLED` default OFF. Run GitHub [44155285675](https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/44155285675) PASS Node + 9 tests Python (25 test cases en el código, cero llamadas reales al proveedor).
5. **Cloudflare candidato:** Worker existente `cerebro-fact001-github-oidc-enroll-lab-eu`. Versión estable `c9322b54-adb0-4795-b5eb-4680bf02b6af` mantiene **100 %**; versión V10 `f25be79f-a70b-40af-bf63-b77d6fec745a` con nuevo endpoint `/v1/factory/image-review` y AI binding está al **0 %**, deploy `d9fba999-087d-4c56-86bb-3173d441aad4`. Flags `VISION_QA_ENABLED=false`, `VISION_QA_COST_VERIFIED=false`. Se conservan cinco bindings antiguos. V9 `0b219c00-...` se creó pero Cloudflare rechazó desplegarlo con splits por diferencia de exports; V10 corrigió la compatibilidad y la distribución 100/0 se verificó físicamente. No rutas públicas nuevas, ni credenciales nuevas.
6. **Automatización existente reutilizada:** `UMS-001 · Guardar imágenes en Drive` (task existente) actualizada, NO se creó otra plaza. Cada 4h revisa nuevas entregas de Productora, archiva los originales con dedupe, intenta inspección visual real cuando el contenido esté accesible y marca `REJECTED_VISUAL` o `QA_HOLD`. Nunca aprueba publicación. Ejecutada inline en este turno: solo se detectó el último run `44147612208` ya archivado, Drive con 4 JPEG y el ZIP, sin nuevas altas ni duplicados. La primera ejecución futura de la nueva inspección visual aún no está certificada.

## BLOQUEADO / HUMAN_REQUIRED (solo si se necesita)
- Cloudflare Workers AI tiene 10 000 neuronas/día gratis, pero en plan Paid el exceso se factura. La llamada de lectura de suscripciones del conector devolvió HTTP 403. Sin verificar cuota/plan y consumo disponible, no habilitar inferencia que pueda facturar. Fuente pública: https://developers.cloudflare.com/workers-ai/platform/pricing/
- El modelo Meta Llama Vision requiere aceptar licencia del proveedor con primer prompt `agree`; **no se han aceptado términos**. Fuente https://developers.cloudflare.com/workers-ai/models/llama-3.2-11b-vision-instruct/
- Falta probar con los JPEG defectuosos una llamada real del inspector, calibrar positivos/negativos, segundo revisor independiente o tribunal y validación del umbral. No es legítimo declarar `visual_qa=PASS` a una foto desconocida solo por un resultado de modelo no calibrado.
- Falta conectar los consumidores NEWS/Brevo/WordPress/Social a `require_reuse_approval` y validar QA/rollback E2E.

## ESTADO
`VISION_AUDITOR_CODE=DEFINED_AND_CI_TESTED`
`BRIDGE_CANDIDATE=UPLOADED_0_PERCENT`
`LIVE_VISION_INFERENCE=OFF`
`AUTO_ARCHIVE=ENABLED_SCHEDULED`
`AUTO_VISUAL_INSPECTION_TASK=UPDATED_PENDING_FUTURE_RUN_PROOF`
`REUSE_GATE=FAIL_CLOSED_LAB`
`COST_ADDITIONAL_NO_NEW_AI_CALLS=0`
`NEWS001_BREVO_SEND=OFF`
`PROD=HOLD`

## PRÓXIMO BLOQUE
Verificar billing/quota sin precio adicional; aclarar licencia Meta si procede; una sola inferencia controlada gratuita y con recibo sobre el JPEG B2C rechazado (no usar clientes); calibración; integrar 2º revisor y prueba positiva; firmar atestación exacta SHA256/empresa/motor/solicitud; ejecutar QA completa y promover gradualmente únicamente si todos los gates están verdes. NUNCA forzar V10 al 100% para saltar incompatibilidades.

Se ha preservado App, CRM, Supabase, WordPress, SEO, redes, brevo, DNS, main, tráfico/worker estable y biblioteca UMS-001 existente.
