# TAX-001 Backup

Estado: PARCIAL_VERIFIED.

El rehearsal local `ops/rehearsal.py` crea un snapshot no destructivo de código, configuración, contratos, observabilidad y runbooks de TAX-001, calcula SHA-256 por fichero y valida el snapshot antes de restaurarlo en un directorio temporal.

No incluye los artefactos canónicos externos AW/AV/BH porque siguen sin estar disponibles/verificados en el repositorio. Por ello `manifest.json -> backup.verified` permanece en `false` y el motor sigue fail-closed para promoción.

No toca App, CRM, Supabase ni PROD. Coste adicional: 0 €.
