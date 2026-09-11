# CEREBRO OS — 177/177 LAB GREEN

Fecha: 2026-09-11
Entorno: LAB
Rama: `cerebro-engine-factory-v0`

## HECHO

- Registry canónico: 177 `engine_id` únicos.
- Cobertura lógica: 177/177.
- Catálogo de evidencia LAB: 177/177.
- Cada `engine_id` dispone de comportamiento/contrato dedicado cubierto por tests ejecutables o, para FACT-001, smoke de Factory.
- `system_gate` exige 177 filas canónicas y solo devuelve GREEN si todas están en `LAB_GREEN` o `CONFIRMED_OPERATIONAL`.
- CI de referencia: GitHub Actions run `34640108469`, HEAD `e0e9fdac8f45ec7465d15e36e9de23afd85852e8`: unit tests GREEN, Factory smoke GREEN, job GREEN.
- Human Exception limitado a: LEGAL_REQUIRED, SIGNATURE_REQUIRED, LOW_CONFIDENCE, HIGH_RISK, POLICY_CONFLICT, SECURITY_INCIDENT, MONEY_LIMIT, CUSTOMER_HUMAN_REQUEST.
- Multiempresa preservada mediante `company_id`/tenant scope en los contratos que manejan datos o ejecución.
- Coste adicional 0 € preservado como default; gasto fuera de límite usa MONEY_LIMIT.
- Trading permanece aislado: LAB/PAPER permitido por contratos; ejecución REAL no se promueve desde el controlador LAB.
- App/CRM no han sido rehechos ni desplegados: se han creado wrappers/contratos y gates de preservación.

## PARCIAL / NO CONFUNDIR CON OPERATIVO PROD

`LAB_GREEN` significa que el contrato y comportamiento implementado en esta rama tienen evidencia automatizada. No significa por sí solo:

- que una integración bancaria, notarial, fiscal, WordPress, red social, firma digital, proveedor, correo, voz o API externa esté conectada y autorizada;
- que existan credenciales reales disponibles;
- que PREPROD o PROD hayan sido promovidos;
- que todos los criterios legales/fiscales/hipotecarios reales estén cargados como reglas vigentes;
- que App/CRM PROD hayan sido modificados;
- que el repositorio actual sea necesariamente el destino definitivo de CEREBRO OS.

## GATES SIGUIENTES PARA PROMOCIÓN

Para cada motor/capacidad que vaya a salir de LAB se mantiene la secuencia:

1. Inventario y dependencia real.
2. Contrato vigente y owner.
3. Credenciales/permisos autorizados, si aplican.
4. Datos/reglas reales con procedencia.
5. Tests de integración.
6. Evaluación y tribunal.
7. Observabilidad y coste medido.
8. Backup, restore, rebuild y rollback verificados.
9. PREPROD cuando aplique (excepto el workstream de PREPROD de App cancelado por decisión del proyecto).
10. Comparación OLD vs NEW.
11. Promoción gradual/feature flag/canary.
12. PROD únicamente tras todos los gates.

## REGLA DE CONTINUIDAD

No borrar ni rehacer lo existente. Continuar siempre:

CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR.

El siguiente trabajo ya no es “crear los 177 IDs”: es convertir, uno a uno y con evidencia externa cuando corresponda, `LAB_GREEN → integración validada → PREPROD_GREEN/PROD_CANDIDATE`, sin tocar App/CRM/PROD fuera de gates.
