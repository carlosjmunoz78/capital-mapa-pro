# CE-05 · CP71 · Endurecimiento de checkpoints LRN (LAB)

## Alcance

Cambio aditivo de compatibilidad en `learning/improvement_checkpoint_store.py`. El esquema SQLite existente se preserva, sin migración ni borrado. Se mantiene la clave compuesta `(company_id, environment, version)` para preservar los contratos y se exige que un registro con la misma clave tenga **el mismo perfil de autonomía**.

## Defecto OLD reproducido

La implementación previa hacía UPSERT de `autonomy_profile`, `status` y `stage_results_json` sin comprobar la versión anterior. Con un identificador existente se podía sustituir un `GREEN` por otra evidencia, borrar etapas, cambiar un perfil de autonomía o declarar GREEN con menos de 12 etapas completas. Dos conexiones separadas reproducen el conflicto.

## NEW

- Valida que las etapas estén en orden canónico, sin duplicados, y que los resultados incluyan evidencia cuando el estado es GREEN.
- Impide declarar un checkpoint completo GREEN sin 12 etapas correctas.
- Protege el perfil y los resultados de pasos confirmados, y bloquea la truncación.
- Permite el progreso legítimo de la **última etapa no resuelta**, incluida su sustitución WAITING → GREEN y el avance a la siguiente etapa.
- Utiliza `BEGIN IMMEDIATE` para una lectura/comparación/escritura atómica ante otras conexiones SQLite.
- Respeta `save`, `load`, `delete`, `close` y el esquema anterior. `delete` explícito se mantiene por compatibilidad, pero su autorización operativa corresponde al runtime supervisor.
- Nunca autoriza publicaciones, trading, cambios legales, coste ni promoción a PROD.

## Evidencia

- `test_old.log`: 22 tests ejecutados, 7 fallos que reproducen el defecto.
- `test_new.log`: 22 tests ejecutados, 22 correctos (5 pruebas originales del store, 7 pruebas originales de runtime y 10 controles CP71).
- No se modifican tablas existentes ni se activa CE-11 o JARVIS Gateway.
- El checkpoint no es una firma criptográfica externa ni un journal inmutable frente a un administrador de base de datos.

## Rollback

Mantener original de `improvement_checkpoint_store.py` respaldado en el paquete y revertir solo el commit LAB CP71. Verificar que el árbol coincide con el anterior. No aplicar migraciones.

## Estado

**LAB probado localmente.** Pendiente evaluación remota dentro de identidad y runtime autorizados. Coste adicional de infraestructura 0 €.