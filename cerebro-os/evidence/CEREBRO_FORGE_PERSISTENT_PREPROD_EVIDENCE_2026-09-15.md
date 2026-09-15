# CEREBRO FORGE · PERSISTENT PREPROD EVIDENCE

Fecha: 2026-09-15
Estado del documento: HECHO / evidencia técnica registrada

## Alcance

Este documento fija la evidencia del entorno PREPROD persistente de CEREBRO FORGE para Advisory. No habilita PROD, no modifica App/CRM/Supabase PROD y no concede autonomía global.

## Evidencia física demostrada

- project_id: `cerebro-forge`
- project_number: `15609183753`
- region: `europe-southwest1`
- Cloud Run service: `cerebro-advisory-preprod`
- ready revision: `cerebro-advisory-preprod-00004-k4f`
- Git commit / image tag: `14a2f25cf3dcb46c4f1e624912f5ce3a81c59187`
- image digest: `sha256:ad1654c381860db036c02365d8aea5ed7bb5a3de16a37608d4a29a7cdb972f6a`
- runtime service account: `cerebro-forge-runtime@cerebro-forge.iam.gserviceaccount.com`
- GitHub Actions run: `35001283326` / `CEREBRO FORGE PREPROD` / run #11
- GitHub Actions artifact: `cerebro-forge-preprod-14a2f25cf3dcb46c4f1e624912f5ce3a81c59187`
- artifact digest: `sha256:7340e9a10d84ed4ed507dfe9f01226de641c4b704bfda779882dd66ef60db3e6`

## Gates demostrados en verde

El run #11 terminó `success` con estos pasos verdes:

1. Checkout.
2. WIF GitHub -> Google Cloud.
3. gcloud setup.
4. Verificación de proyecto y deploy service account.
5. Verificación de Artifact Registry.
6. Docker auth.
7. Build de imagen.
8. Rehearsal físico aislado previo a despliegue.
9. Push de imagen.
10. Despliegue privado de Cloud Run PREPROD.
11. Verificación de revisión, digest inmutable, runtime service account y contrato exacto de aislamiento.
12. Captura de evidencia.
13. Upload del artefacto de evidencia.

## Contrato de aislamiento demostrado

La revisión desplegada exige exactamente:

- `CEREBRO_ENV=PREPROD`
- `CEREBRO_PREPROD_MODE=persistent_candidate`
- `CEREBRO_EXTERNAL_WRITES=disabled`
- `CEREBRO_APP_CRM_ACCESS=disabled`
- `CEREBRO_PROD_CREDENTIALS=disabled`
- `CEREBRO_CUSTOMER_DATA=disabled`

El rehearsal previo además se ejecutó con red Docker deshabilitada, filesystem read-only, capabilities eliminadas y `no-new-privileges`.

## Estado canónico tras este bloque

- `PERSISTENT_PREPROD_ENVIRONMENT=TRUE` — HECHO, demostrado físicamente.
- `PREPROD_ENABLED=NO` — se mantiene cerrado hasta completar validación funcional persistente y cierre de promoción.
- `CAPABILITY_GREEN_GLOBAL=NO` — sin cambios.
- `AUTONOMY_GREEN=NO` — sin cambios.
- `PROD_ENABLED=NO` — sin cambios.

## Pendiente antes de PREPROD_ENABLED=TRUE

- Ejecutar validación funcional dentro de infraestructura GCP PREPROD, no solo en el runner efímero de GitHub.
- Confirmar los tres casos representativos y cobertura 12/12 con evidencia persistente.
- Registrar comparación LAB/ephemeral vs GCP PREPROD.
- Registrar rollback/rebuild operativo del candidato persistente.
- Mantener coste medido / no inventado y política fail-closed.

## Política de preservación

Se mantiene la secuencia:

`CONSERVAR -> ENTENDER -> ENVOLVER -> PROBAR -> MEJORAR -> MIGRAR`

No se toca App, CRM, Supabase PROD, Notion, WordPress, SEO, Training, automatizaciones ni Trading PROD por este cambio.
