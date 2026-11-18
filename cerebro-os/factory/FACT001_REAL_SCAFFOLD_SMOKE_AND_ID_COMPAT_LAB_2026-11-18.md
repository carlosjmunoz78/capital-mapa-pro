# FACT-001 · Prueba física del generador existente y compatibilidad de identidades

**Fecha:** 18/11/2026 · **Ámbito:** laboratorio aislado, Fénix. **NO PROD**.

## Inventario y preservación

- Fábrica principal ya existente en la rama `cerebro-engine-factory-v0`: `cerebro-os/factory/factory.py`, `universal_media_hook.py`, `universal_media_enrollment.py` y `engine_manifest.schema.json`.
- Identificadores Git blob del original comprobados antes de la prueba: `factory.py=bd2297a0cbe8018840c9b3f56367914f98748855`, `universal_media_hook.py=ec5d6db39e8a101ddfaed586ae07794411a90a3e`, `universal_media_enrollment.py=b30dcd6bf3ea2226a1722cd3e0b059703bc6bce9`, `engine_manifest.schema.json=42dda5556833c064ad9625ea2015d058bf824d81`.
- Copia de rama exacta para cambios **SOLO en `cerebro/fact001-identity-compat-lab-20261118`**. Ni rama origen ni `main` modificados. Reversión: cerrar la PR / descartar esta rama; la ejecución en producción queda intacta.

## Ejecución y calidad (local sin GitHub Actions)

1. Los tres módulos Python originales se reprodujeron y verificaron mediante Git blob SHA1 contra los archivos reales del repositorio; no es un simulacro de una implementación alternativa.
2. Se ejecutó `factory.scaffold` de forma aislada para `FACT-DEMO-20261118`, `company_id=fenix`, sin variables de Cloudflare ni conexión de red, produciendo 9 archivos, 12 carpetas estándar, manifiesto y evento FACT001_ENGINE_CREATED.
3. El manifiesto generado pasó `jsonschema.Draft202012Validator` contra el esquema original; `status=DEFINED_NOT_BUILT`, `enrollment_status=PENDING_FACTORY_IAM_TRANSPORT`, `media_dispatch_enabled=false`.
4. 15/15 ensayos funcionales y de seguridad superados sobre el código original: identidad, carpeta, contratos, separación de empresa, duplicados, prohibición de gastos/publicación y transporte firmado simulado con un `FakeResponse`, **sin enviar peticiones de pago**.
5. Se detectaron inconsistencias reales: el validador original aceptaba IDs incorrectos como `---`, pero UMS rechazaba `3RD-001`, identificador existente en el inventario canónico.
6. La candidata modifica **solo dos expresiones regulares**, preservando IDs legítimos que empiezan por dígito cuando contienen letras y tienen formato válido. Se contrastó contra 177 IDs canónicos + 13 semillas; todos compatibles, ningún identificador descartado.
7. Se ejecutaron 6/6 pruebas nuevas desde `tests/test_fact001_identity_compat_lab.py` (SHA Git `a51c27f3109b236848f07dcec1b948384934bfc0`): los 177 motores se generaron en un directorio temporal, todos permanecieron pendientes de IAM y sin pagos. No fueron instalados ni activados en producción.
8. Tras corregir un salto de línea en la rama candidata, se ejecutaron de nuevo las 15/15 pruebas originales del smoke y las seis nuevas: **21 pruebas locales correctas**. No se reclama aprobación GitHub Actions (temporalmente bloqueado).

## Dependencias cloud existentes verificadas sin modificarlas

- Cloudflare Queue LAB `cerebro-fact001-ums001-enrollment-lab-eu` ID `45f17e040bcb4c10a509f31b1460da49`: **EXISTE**, un consumidor identificado como `cerebro-fact001-ums001-issuer-provisioner-lab-eu`.
- Worker LAB FACT Gateway `cerebro-fact001-gateway-lab-eu-20261109` y provisioner constan en inventario Cloudflare.
- El Gateway/provisioner tienen referencias de claves de firma configuradas. **Esto NO acredita que el runtime Python disponga de dichas claves**, que haya enviado un alta positiva o que UMS haya autorizado su uso. Los valores secretos NO se han consultado ni transmitido.
- Alta real positiva FACT Python → cola → provisioner → acuse IAM: **PENDIENTE**. La cola no se alteró, no se hizo POST de ensayo sin identidad, no se creó Worker adicional ni motor con privilegios.

## Seguridad, gates, coste, rollback

- Cumple `company_id`, `engine_id`, `environment`, `version`; pruebas actuales solo para Fénix LAB.
- No modifica App/CRM/WordPress/DNS/Supabase PROD, trabajos HOLD de UMS ni medios. No se hicieron publicaciones ni llamadas de IA de pago. **Nuevas suscripciones: 0 €**, consumo de herramientas existentes no cuantificado.
- El generador crea manifiestos y artefactos, **no convierte por sí solo motores en autónomos**. No cuenta como alta física de 177 motores.
- Pruebas de rollback de producción, backup externo, tribunal, financiación/observabilidad y alta real IAM todavía no acreditadas. Antes de un merge: ejecutar testes OLD vs NEW en runner permitido, evidencia de firma positiva real y rechazo de suplantación, permisos, coste medido y rollback integral.
- Una limitación por resolver separadamente: `scaffold` todavía no usa escritura atómica integral; si un hook falla después de crear carpetas, se requiere rollback/rebuild explícito. No se modifica este comportamiento en esta PR de compatibilidad para minimizar riesgo.

## Changelog / próxima ejecución

- `FACT-001-IDENTITY-COMPAT-LAB`: regla de identidad unificada en `factory.py` y `universal_media_enrollment.py`, nueva suite de seis pruebas.
- Próximo gate prioritario: acoplar la identidad real del runtime Python a la firma FACT sin reutilizar credenciales entre motores; confirmar ACK verificable desde el Gateway; seguir usando un único runtime compartido y sin acciones de pago.
- Estado de autonomía: **SCaffold real probado localmente; Cloudflare enrollment real = BLOQUEADO POR IAM DE RUNTIME; PROD = HOLD**.

## 18/11/2026 · FACT-001 preparación atómica añadida sin alterar la rama original
- `factory.scaffold` construye primero en un directorio temporal privado del mismo filesystem y, solo tras completar todos los hooks y archivos, mueve la carpeta completa al destino. La reserva `.ENGINE.factory.lock` usa creación exclusiva; una excepción limpia staging y libera la reserva. En un crash abrupto, la reserva podría quedar obsoleta: recuperación manual con verificación de que no hay otro proceso, nunca eliminación automática.
- El hook de medios UMS se invoca inicialmente con **environ limitado a CEREBRO_COMPANY_ID** (sin credenciales), generando solamente outbox y un estado PENDING. Solo después del commit se evalúa si el runtime físico dispone de cuatro variables IAM necesarias para intentar el envío; no se intenta envío con configuración parcial ni se hacen reintentos automáticos.
- No hay ninguna operación REAL contra la cola de Cloudflare en estas pruebas. Para probar la secuencia de envío se usa transporte ficticio que verifica el instante de commit; el resultado de esa prueba no es un ACK real.
- Ensayos nuevos: hook tardío con fallo => 0 carpetas incompletas, 0 locks; concurrencia con dos escritores => exactamente uno obtiene motor completo; fallo de red tras commit => carpeta completa + recibo `HOLD_ENROLLMENT_TRANSPORT`; sin IAM completo => 0 peticiones; no reemplazar motor previo.
- **27/27 pruebas físicas locales VERDES:** 15 regresiones + 12 pruebas de identidad, protección, fallo y concurrencia. Ambos archivos fuente y test cotejados con Git blob de la revisión actual, `factory.py=89d5c42b0d600ccd6589b55cde00e6e13e01e894`, `test_fact001_identity_compat_lab.py=12ce2bb852f08647426b6c65ac010fbc408ec81c`.
- Comparación OLD vs NEW por ejecución del mismo engine_id `FACT-OLDNEW-001`: **9/9 archivos iguales en contenido** (después de normalizar solo `issued_at_utc` por ser una marca temporal distinta), `status=PASS`. No cambios a los contratos del motor.
- Python `compileall` completado sin errores. Evidencia machine-readable: `cerebro-os/factory/FACT001_ATOMIC_SCAFFOLD_EVIDENCE_LAB_2026-11-18.json`. El análisis de fuente Cloudflare confirmó que el Gateway no expone un endpoint de ejecución libre; bridge OIDC autoriza un workflow GitHub específico y el provisioner de la cola exige firma HMAC válida.
- **Gates aún no acreditados:** backup externo, identidad real del runner para alta Cloudflare, confirmación positiva del provisioner, coste medido, tribunal integral, OLD vs NEW Cloudflare real y rollback PROD. Por tanto `FACT-001_AUTONOMY_CERTIFIED=false`, PR DRAFT, sin merge ni deployment.

## Procedimiento de emergencia si falla la construcción
1. El generador debe eliminar staging local y liberar el lock, sin dejar un motor registrado.
2. Si la construcción termina pero no se entrega el evento IAM, conservar la carpeta completa y el outbox, mantener `media_dispatch_enabled=false` y gestionar la recuperación bajo IAM válido.
3. Ante caída abrupta de host, inspeccionar proceso y target antes de retirar manualmente un lock obsoleto. Nunca eliminar la carpeta de un motor preexistente.
4. Reversión de este parche: descartar esta rama candidata; la rama `cerebro-engine-factory-v0` permanece sin modificaciones. **La reversión LIVE de un Gateway o despliegue no está probada y no se declara verde.**
