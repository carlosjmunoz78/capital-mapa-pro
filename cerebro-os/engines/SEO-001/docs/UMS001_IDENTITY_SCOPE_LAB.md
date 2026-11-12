# SEO-001 · Identidad UMS-001 de LAB

Este manifiesto **solo** aprovisiona una identidad de ensayo para usar `IMAGE.SYNTHETIC` mediante el Gateway FACT de CEREBRO. No activa el motor SEO existente, no crea WordPress hooks ni publica imágenes, entradas o páginas. El motor SEO real y su runtime WordPress/STAGING no están conectados hasta que exista una autenticación de runtime específica y una prueba E2E. Prohibido reutilizar credenciales de FACT-001 como token de WordPress.

Las altas FACT-001 usan GitHub Actions OIDC temporal y el control de permisos del Gateway. Se conserva `status=DEFINED_NOT_BUILT` como estado del manifiesto de ensayo; la identidad `ACTIVE` solo significa inscripción IAM del motor en LAB, no SEO operativo.
