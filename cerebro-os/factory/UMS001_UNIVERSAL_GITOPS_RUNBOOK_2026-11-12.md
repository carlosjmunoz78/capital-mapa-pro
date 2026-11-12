# CEREBRO UMS-001 · Cliente universal GitOps LAB

Los motores FACT-001 registrados en el Gateway pueden crear solicitudes de imágenes originales incorporando un archivo JSON INMUTABLE en cerebro-os/media-requests/ENGINE_ID/REQUEST_ID.json. Un único workflow obtiene GitHub OIDC, llama al Gateway universal, consulta recibos y descarga el JPEG privado verificando SHA256, dimensiones y empresa. Los archivos se entregan como artifact privado de GitHub durante 1 día, sin publicación en redes ni web.

Sólo Fénix LAB y motores con manifest válido bajo rama cerebro-engine-factory-v0. Los motores externos siguen necesitando que su runtime hable con CEREBRO Gateway mediante una identidad real; no se permite suplantación por payload. No fusionar a main ni certificar publicación o coste de facturación.
