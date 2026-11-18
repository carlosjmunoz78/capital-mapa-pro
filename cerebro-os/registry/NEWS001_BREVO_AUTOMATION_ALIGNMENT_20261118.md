# NEWS-001 · Reconciliación de las 7 automatizaciones de Brevo · 18/11/2026

## Resultado real de la auditoría
Se han inspeccionado **7 de 7** flujos en el editor autenticado de Brevo sin efectuar mutaciones. **Seis activos y uno inactivo**, todos creados o editados entre mayo-junio 2026. No se ha leído/descargado el HTML integral de cada mensaje: **solo asunto, previsualización textual corta, lista de entrada y espera visibles**. Por tanto, NO afirmar que sus diseños actuales cumplen la identidad de Fénix: la **homogeneidad visual de los 7 correos aún NO está acreditada**.

| ID | Flujo | Lista disparadora | Espera | Estado | Clasificación |
|---|---|---|---|---|---|
| 1 | mensajes tras check list 100 | #2 Particulares · Hipotecas | P1D | active | RESOURCE_FOLLOWUP_B2C |
| 2 | inmo mensajes tras check list | #6 Inmobiliarias · Partner Hipotecario | P1D | active | RESOURCE_FOLLOWUP_B2B |
| 4 | mensajes tras checklist autopromotor | #11 Leads - Hipoteca Autopromotor | P1D | inactive | RESOURCE_FOLLOWUP_B2C |
| 5 | lanzamiento calculadora | #12 Inmobiliairas colaboradores | P1DT1H | active | TOOL_ANNOUNCEMENT_B2B |
| 7 | EMAIL CONTACTOS Q NO RESPONDEN | #14 Llamado sin contacto | PT3H | active | FOLLOWUP_NO_RESPONSE |
| 8 | Mensaje de bienvenida | #15 NUEVOS LEADS PARTICULARES | PT1H | active | LEAD_ACKNOWLEDGEMENT |
| 9 | NEW LETTER PARTICULARES | #10 Particulares · NEW LETTER | PT4H | active | LEGACY_NEWSLETTER_B2C |

## Hallazgo principal
- **#9 NEW LETTER PARTICULARES está ACTIVA pero usa lista histórica #10 (23 miembros)** y un texto de junio, no la lista de particulares nuevos NEWS001 #17 (0 miembros). Es incompatible con la política actual de no reutilizar campañas ni particulares antiguos. Ningún lead nuevo de NEWS001 deberá añadirse a #10. **No se ha pausado #9** (no existen comandos de actualización de automaciones en el conector Brevo disponible y el navegador Opera conectado solo admite lectura); proponer pausa controlada cuando haya snapshot restaurable y comprobación de dependencias.
- **#8 Mensaje de bienvenida está ACTIVA, usa #15 (11 miembros), tras una hora**, y sirve para confirmar recepción del contacto, NO para entregar la newsletter editorial completa. En caso de que la misma persona entre también en NEWS001 #17, no debe recibir dos mensajes de bienvenida equivalentes.
- **#1/#2/#4/#5/#7 son seguimientos de guías, herramienta o contacto sin respuesta**: mantener su lógica de negocio, no convertirlos en newsletters largas. #4 está inactiva: NO reactivar por la auditoría.
- **#17 y #18 ya existen en Brevo con 0 miembros cada una**. No tienen en estos siete flujos una automatización que entregue el nuevo diseño de CEREBRO a sus altas.

## Contrato editorial homogéneo
- **Newsletter semanal/editorial:** único diseño canónico generado por CEREBRO (10 bloques reales, 13 enlaces, logo oficial, imagen principal distinta B2B/B2C, responsive), NO las dos maquetas rosa/cortas rechazadas.
- **Bienvenida:** edición vigente de ese diseño completo entregada al nuevo lead con opt-in verificado y deduplicación; NO enviar innecesariamente una bienvenida breve y además una newsletter completa al mismo instante. Luego entrará en su calendario editorial semanal.
- **Seguimiento de recurso/lead:** mensajes más breves, pero encabezado/logo, pie, nombres, acento naranja #FF5F00, tipografía legible, enlaces y CTA coherentes. No imponer 10 bloques a un simple acuse de recibo.
- Separación clara B2B vs B2C, Salinas nunca, no importar históricos particulares, respetar bajas/rebotes, y usar la marca del Manual 2025. Identificar consentimiento comercial de formulario marcado explícitamente, sin inferir de la casilla de privacidad.
- Roles/cadencia: `ACK_LEAD`, `RESOURCE_FOLLOWUP`, `NO_RESPONSE`, `CURRENT_NEWSLETTER_ON_ENTRY`, `WEEKLY_ISSUE`. Evitar envío duplicado por idempotencia del mismo email/issue/perfil.

## Estrategia de no rotura
Conservar las seis activas y la inactiva en su estado actual hasta extraer el backup de cada flujo (disparador, pasos, emails HTML, opciones, enlaces, condiciones). Comparar `OLD vs NEW` con casos de prueba y puesta en marcha paralela. Para reemplazos: desactivar primero los destinos/activaciones nuevas en laboratorio; verificar doble disparo, revocación de consentimiento y rollback; después promoción gradual. El circuito NEWS001 está en LAB y **no envía**.

## Lo que sí existe y lo que falta
- HECHO: inventario completo de 7 flujos, 9 listas revisadas, clasificación por propósito, contratos de diseño y rutas #17/#18 en el motor LAB.
- PARCIAL: generación de dos newsletters en GitHub LAB; pruebas del enrutador.
- BLOQUEADO: edición de workflows en Brevo desde el conector actual, que solo permite consultar y administrar listas; la sesión Opera disponible solo lee páginas. El permiso del propietario no convierte un conector de lectura en uno de escritura. **Ni se pausó #9, ni se activaron los envíos nuevos**.
- Próxima prueba: extracción segura de HTML completos y configuración de disparadores, comprobación de opt-in en un lead NUEVO, puesta en marcha paralela y test real de entrega y baja. No cambiar App/CRM/WordPress PROD.

## Evidencia
- URL de editor por flujo: `https://app.brevo.com/automation/edit/{ID}` para 1,2,4,5,7,8,9, visitados físicamente el 18/11/2026.
- IDs de destino Fénix creados: B2B **18**, B2C **17**, sin miembros.
- Fuente canónica: `cerebro-os/engines/CEREBRO-NEWS-001/editor/` y ejecución CI de generación verificada 44280104275.
- Documento estructurado: `cerebro-os/registry/NEWS001_BREVO_AUTOMATION_ALIGNMENT_20261118.json`.

**Coste nuevo: 0 €; sin campañas ni correos comerciales enviados por esta revisión.**
