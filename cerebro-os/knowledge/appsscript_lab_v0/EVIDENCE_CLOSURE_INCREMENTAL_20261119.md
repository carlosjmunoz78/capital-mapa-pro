# Cierre operativo incremental · 2026-11-19 · LAB

Google Apps Script se ejecutó con el encolado ya instalado. El límite de 600 entregas por día UTC se alcanzó con 527 de Facebook y 73 de Instagram. LinkedIn y SEO todavía conservan 0 recibos. Los 600 registros tienen claves únicas y quedan 1.122 pendientes de las 1.722 asignaciones. La ejecución incremental de 10:51:28 UTC añadió cero nuevas filas y dejó un solo temporizador de continuación y un activador de edición. Por código, la reanudación con cuota agotada se agenda después del siguiente inicio de día UTC. [Auditoría](https://docs.google.com/spreadsheets/d/1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc/edit#gid=1266644722)

El permiso Lector de la hoja privada se confirmó en Drive para la identidad de servicio dedicada `cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com`. La hoja mantiene acceso general restringido. La concesión IAM al operador tiene un solo permiso, `iam.serviceAccounts.getAccessToken`, sobre esa identidad concreta, con expiración 2026-11-19 11:57:01 UTC. Los tokens emitidos con `spreadsheets.readonly` tienen 600 segundos de vida. No se crearon claves. Sheets API e IAM Credentials API están habilitadas en FORGE.

| UTC | Empresa y ámbito | Resultado del consumidor autenticado |
| --- | --- | --- |
| 10:59:15.959 | other-company / Facebook | DENIED, antes de consultar Sheets |
| 10:59:16.490 | fenix-capital / Facebook / versión ajena | DENIED, antes de consultar Sheets |
| 10:59:19.719 | fenix-capital / Facebook / FB-00.SA-001 | READ_VERIFIED. SHA-256 `0e3166ac244cf80290eb3242711d04260074f629d733d21673aeb57c6c044416` |
| 10:59:21.443 | fenix-capital / Instagram / IG-00.SA-001 | READ_VERIFIED. SHA-256 `66b8ee860a1d9a6508facf133aed201fbdf537541b7b4f59c5e8a9f1a46c886b` |
| 10:59:23.269 | fenix-capital / LinkedIn / LI-00.SA-001 | PENDING_RECEIPT. Paquete retenido |
| 10:59:25.787 | fenix / SEO / SEO-D01:SPECIALIST:01 | PENDING_RECEIPT. Paquete retenido |

El canario en Cloud Shell informó `verified_reads=2` de las tres requeridas y la prueba unitaria del adaptador pasó. Queda repetir el canario después de recibir un recibo de LinkedIn o SEO y conectar el lector al runtime LAB con su identidad propia, política y auditoría duradera. La cuenta de servicio y su permiso Lector ya están preparados. Agentes con consumo demostrado y certificaciones válidas en este cierre: cero.

Los archivos de Apps Script y el manifiesto de Google conservan su configuración original. FACT-001 se amplió en la rama DRAFT con entrada de inventario explícito y deduplicación de solicitudes. Pasaron cuatro pruebas Python en Cloud Shell y el ensayo sintético de dos empresas y tres departamentos. Los puntos de alta de creadores externos todavía deben integrarse. Las áreas sin identidades verificadas tienen solicitudes de investigación en `research_requests.lab.json`. Sin despacho, cambios en producción ni certificaciones.
