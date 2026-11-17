# CEREBRO · Productora universal: acceso de motores por capacidad (LAB)

**Orden del propietario (17/11/2026):** cualquier motor legítimo de CEREBRO debe poder **solicitar** imágenes, vídeo, audio y recursos creativos de la Productora, sin necesidad de crear servidores o nuevas suscripciones por motor.

**Ejecución preservadora:** No habilitar acceso público ni una lista global sin autenticar; utilizar el mecanismo EXISTENTE `FACT-001` firmado con GitHub OIDC, identidades registradas y Gateway UMS-001 por service binding. La implementación actual de alta certifica en LAB sólo `IMAGE.SYNTHETIC`. VIDEO/AUDIO son capacidades futuras sujetas a sus propios contratos y presupuesto; NO marcarlas operativas.

**Contrato por motor:** `company_id`, `engine_id`, `environment`, `version`, `request_id`, `capability_id`, `rights_profile`, `budget`, `publication=false`. Para una nueva empresa, emitir credencial aislada a empresa/entorno/capacidad. Alta en `cerebro-os/engines/<engine-id>/manifest.json` con capability `IMAGE.SYNTHETIC`, ejecutada mediante `cerebro-fact-ums001-oidc-lab.yml` (OIDC efímero).

**Permisos:** alta no implica autorización de publicación, IA de pago, datos sensibles o accesos a otros motores; gastos 0 EUR por defecto, sin recarga; imágenes para newsletter sujetas a QA visual/de marca/derechos y test móvil. La factura de Workers AI o uso de plan debe verificarse antes de autonomía; evitar consumos accidentales.

**NEWS-001:** motor en el sistema newsletter identificado como `CEREBRO-NEWS-001` (FACT/UMS ID), con B2C/B2B independientes, *una edición de prueba por audiencia*. Sin ubicación textual, numeración, vídeo semanal ni contenidos inventados. En imágenes se permite tipografía legible; personas españolas de apariencia europea como preferencia creativa, sin atribuir identidad real ni exigir exclusión en contratación.

**Gates:** registrarse con prueba OIDC; emitir dos briefs editoriales 0 EUR; enviar por GitOps sólo tras alta ACTIVE; verificar `PRIVATE_ASSET_RECEIVED` y SHA256; registro QA de versión de origen; integrar en borradores Brevo sin envío; conservar estado del router DeepSeek y de todas las demás integraciones. No usar otro motor como sustituto para eludir permisos.

**Rollback:** mantener envíos OFF; cualquier fallo de enrollment detiene solicitudes de NEWS-001; no quitar concesiones de otros motores; restaurar GitOps en rama sin fusionar main.