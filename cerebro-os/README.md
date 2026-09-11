# CEREBRO OS · Engine Factory V0

Estado: implementación aislada en rama `cerebro-engine-factory-v0`. No toca App, CRM ni PROD.

## Objetivo
FACT-001 genera scaffolds estándar de motores lógicos compartiendo runtime. Cada scaffold incluye manifest, config, contratos, permisos, políticas, eventos, jobs, API, tests, evaluación, observabilidad, coste, backup, rollback, rebuild y documentación.

## Regla de promoción
Ningún motor se considera operativo por existir un scaffold. Debe pasar tests, evaluación, observabilidad y gates de promoción.

## Alcance V0
- Generador determinista sin IA de pago.
- Engine Registry local versionado.
- `company_id`, `engine_id`, `environment`, `version` obligatorios.
- HUMAN_REQUIRED canónico.
- Sin servidores por motor.
- Cero coste adicional por defecto.
