# UMS-001 · Inspección de imagen por IA · candidato LAB (17-11-2026)

Este módulo implementa una llamada real a la API de Workers AI mediante env.AI.run() cuando recibe un JPEG privado íntegro, con AI binding, habilitación expresa y coste comprobado. El modelo inicial es @cf/meta/llama-3.2-11b-vision-instruct, condicionado a aceptación legal del proveedor. **ESTÁ DESHABILITADO** mientras no pueda certificarse el plan/cupo gratuito: el conector Cloudflare respondió HTTP 403 al consultar suscripciones; no se han lanzado inferencias ni aceptado términos de Meta.

Primero bloquea hashes conocidos; revisa anatomía, brazos, manos, caras, textos falsos, deformaciones y coherencia de escena. Fallos de modelo, respuesta parcial, ausencia de imagen o incertidumbre dan QA_HOLD. Un único modelo, incluso indicando PASS, da solo QA_CANDIDATE_UNCALIBRATED: nunca autoriza envío, reutilización, SEO/WordPress/Meta ni publicación. La solución de aceptación autónoma exige un segundo revisor independiente, calibración en imágenes buenas/malas y conexión con el Gateway y consumidores. El código es una preparación del inspector, no una integración ya activa.

Coste: 0 € adicional en este commit (solo tests offline). Sin suscripciones ni cambios en producción. Los originales siguen en Drive. No promover el módulo a PROD o conectar a consumidores sin E2E y rollback.
