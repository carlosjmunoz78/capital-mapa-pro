# CEREBRO OS · Continuous Improvement V0

Estado: IMPLEMENTADO EN RAMA / PENDIENTE DE CI Y PROMOCION.

## Contrato
CEREBRO no cambia por cambiar. Observa, mide, propone, prueba, compara y solo promociona una variante que demuestra mejora con evidencia y rollback.

Ciclo: OBSERVE -> MEASURE -> DETECT -> PROPOSE -> LAB -> TEST -> EVALUATE -> TRIBUNAL -> OLD_VS_NEW -> CANARY -> PROMOTE_OR_ROLLBACK -> LEARN.

## Los 10 bloques
1. Inventario de activos mejorables: reutiliza Registry/Company/Engine scope.
2. Contrato de evolucion: company_id, engine_id, environment, version, perfil de autonomia.
3. Metricas: baseline + metrica + direccion MAXIMIZE/MINIMIZE.
4. Observacion: entrada del ciclo y evidencia de baseline.
5. Deteccion: LRN-001 produce aprendizaje/candidatos; el loop consume oportunidades.
6. Propuesta: ImprovementCandidate versionado, reversible y con coste/riesgo.
7. LAB/tests: nunca se salta; Training no promociona directamente a PROD.
8. Evaluacion/Tribunal/OLD-vs-NEW: evidencia obligatoria y mejora estricta.
9. Promocion gradual: PREPROD/CANARY; regresion -> REJECT/LEARN; rollback permanece obligatorio.
10. Automejora perpetua: toda nueva empresa incorpora continuous_improvement en bootstrap.

## Perfiles
- FENIX_SENSITIVE: propuesta/prueba automatizable, promocion requiere humano.
- FENIX_DIGITAL: automatico por defecto dentro de gates, sin coste nuevo ni alto riesgo.
- AUTONOMOUS_VENTURE: automatico por defecto dentro de gates; AION/futuras ventures nacen con el ciclo.

## Fail closed
Coste adicional > 0 -> HUMAN_REQUIRED/MONEY_LIMIT.
Riesgo HIGH o cambio irreversible -> HUMAN_REQUIRED/HIGH_RISK.
Sin mejora medida -> REJECT.
Evidencia incompleta -> error; no promociona.
PROD -> CANARY antes de promocion efectiva.

## No cambios
Este V0 no toca App Fenix, CRM, Supabase PROD, WordPress, secretos ni Trading LAB.
