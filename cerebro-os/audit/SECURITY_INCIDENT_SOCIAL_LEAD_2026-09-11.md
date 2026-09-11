# SECURITY INCIDENT — Social Lead Ingest (READ-ONLY AUDIT)

Fecha: 2026-09-11
Entorno afectado: PROD
Estado: HUMAN_REQUIRED / SECURITY_INCIDENT
Modo de detección: auditoría de promoción CEREBRO OS en solo lectura

## Hallazgo confirmado

La Edge Function activa `social-lead-ingest` tiene `verify_jwt=false` y autentica las peticiones mediante una credencial compartida embebida directamente en el código desplegado. El valor de la credencial NO se reproduce ni se almacena en este documento.

La función usa `SUPABASE_SERVICE_ROLE_KEY` desde entorno para invocar `public.fenix_prod_social_lead_ingest_server`. Esa RPC está concedida a `service_role` (no a `anon`/`authenticated`) y usa idempotencia. Por tanto, la Edge Function constituye la frontera de autenticación de esta ruta y la credencial embebida forma parte crítica de su seguridad.

## Riesgo

Una credencial incrustada en código desplegado debe tratarse como potencialmente comprometida. Si un tercero la obtiene podría intentar invocar el endpoint público de ingestión social. No se ha realizado ninguna prueba ofensiva ni se ha utilizado la credencial.

## NO realizado

- No se ha modificado PROD.
- No se ha rotado la credencial.
- No se ha desplegado una nueva Edge Function.
- No se ha desactivado el endpoint.
- No se han cambiado RPC/grants/RLS.
- No se ha reproducido el secreto en logs/documentación.

## Remediación propuesta, sujeta a autorización explícita

1. Inventariar todos los callers legítimos de `social-lead-ingest` y su mecanismo actual de autenticación.
2. Generar/establecer una nueva credencial mediante secret/vault del entorno, nunca en código.
3. Cambiar la función para leer la credencial desde `Deno.env` y aplicar comparación segura.
4. Actualizar los callers autorizados a la nueva credencial.
5. Probar en entorno seguro / contrato paralelo sin romper la ingestión actual.
6. Rotar/revocar la credencial antigua.
7. Verificar ingestión, idempotencia, observabilidad y rollback.
8. Documentar contrato, owner, runbook y evidencia final.

## Gate

La promoción relacionada con esta superficie queda bloqueada por `SECURITY_INCIDENT` hasta autorización y rotación verificada. El resto de la auditoría puede continuar en solo lectura, pero ninguna escritura en PROD debe ejecutarse como consecuencia automática de este hallazgo.
