# UMS-001 · Runtime SDK para todos los motores de un runtime autenticado · LAB

El cliente común `cerebro-os/runtime/ums001_universal_media_client.mjs` llama **solo** al Gateway FACT mediante `CEREBRO_MEDIA_GATEWAY` (Service Binding) y `CEREBRO_RUNTIME_TOKEN` (Worker Secret de **ese runtime**, no de cada motor). FACT valida el token contra el registro cifrado/privado de emisores, company_id=fenix, LAB, el prefijo permitido del runtime y la identidad ACTIVE de FACT-001. No se confía en IDs públicos sin autenticar. Nuevos motores FACT registrados dentro del mismo runtime/prefijo se incorporan sin Worker nuevo.

API: `capability()`, `request({request_id,prompt})`, `status(request_id)`, `privateJPEG(request_id)`. Ninguna operación publica. El SDK verifica SHA256 en la descarga.

**Este código no es una afirmación de que los runtimes externos existentes estén conectados.** La conexión de cada runtime requiere una identidad y un token propios; el proceso de credencial de Social permanece bloqueado por la capa de seguridad y los flags Social y FACT-RUNTIME-IAM no deben abrirse hasta una verificación real. La ruta GitHub OIDC y la ruta FACT LAB siguen verificadas y separadas.
