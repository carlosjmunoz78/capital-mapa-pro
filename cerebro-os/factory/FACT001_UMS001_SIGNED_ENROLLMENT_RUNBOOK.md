# FACT-001 → UMS-001 · Alta universal automática desde el scaffold · LAB

Código implementado en la rama `cerebro-engine-factory-v0`, sin modificar main ni los motores existentes.

La creación de un nuevo motor ejecuta de forma automática `enroll_factory_engine`, que obtiene `company_id` del contexto firmado de FACT-001 (argumento o `CEREBRO_COMPANY_ID`), genera un evento `FACT001_ENGINE_CREATED`, firma HMAC y lo envía a la única cola `cerebro-fact001-ums001-enrollment-lab-eu` (`45f17e040bcb4c10a509f31b1460da49`), sin generar Workers por motor.

Variables seguras requeridas en el **runtime que realmente ejecuta FACT-001**: `CEREBRO_FACT_ENROLL_EVENT_KEY`, `CEREBRO_CLOUDFLARE_API_TOKEN`, `CEREBRO_CLOUDFLARE_ACCOUNT_ID`, `CEREBRO_FACT_ENROLL_QUEUE_ID`. El valor de firma existe como Cloudflare Worker Secret del Gateway FACT-001, pero **no hay evidencia de que las mismas variables estén inyectadas en el runner Python/GitHub**: sin ellas, genera un archivo de salida `PENDING_FACTORY_IAM_TRANSPORT`, no envía nada, no autoriza medios y no imprime secretos.

El provisioner en LAB verifica HMAC, alcance empresa/motor, unicidad y caducidad del evento; genera una clave Ed25519 por motor, la cifra con AES-GCM en un KV privado y registra la clave pública en el Gateway Universal. Luego envía un canary firmado al ledger de UMS-001; solo tras recibir `REGISTERED_QA_PENDING` marca el alta como `ACTIVE`. Sin coste de modelos ni publicación.

**Evidencia disponible:** Gateway y provisioner desplegados; una petición de alta SIN firma válida fue rechazada `FACT_EVENT_SIGNATURE_DENIED` y no generó registro. **PENDIENTE de verificar:** alta positiva desencadenada desde FACT-001 runtime (falta acceso a las credenciales desde ese runner), firma positiva y paso al generador real de imágenes para motores genéricos; NO afirmar que la autonomía universal esté terminada.

Regla: no per-engine Worker, no acceso público ni autoactivación para otros tenants; LAB limitado a `fenix` hasta auditar aislamiento multiempresa.
