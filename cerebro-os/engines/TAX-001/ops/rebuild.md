# TAX-001 Rebuild

Estado: PARCIAL_VERIFIED.

`ops/rehearsal.py` restaura en un directorio temporal el snapshot de código/configuración/contratos/observabilidad/runbooks y exige igualdad exacta de los SHA-256 calculados antes y después.

Alcance demostrado: paquete lógico TAX-001 en LAB.

Fuera de alcance aún: reconstrucción de los artefactos canónicos AW/AV/BH y su `corpus_lock` BOUND. Mientras esos artefactos no estén materialmente disponibles y sus hashes no estén verificados, `manifest.json -> rebuild.verified` permanece en `false`.

No toca App, CRM, Supabase ni PROD. Coste adicional: 0 €.
