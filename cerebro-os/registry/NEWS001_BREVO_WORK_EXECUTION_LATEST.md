# NEWS001 · Brevo Work Execution · 18 November 2026

## Current checkpoint

| Task | Status | Real ID / evidence | Cost | Next action |
|---|---|---|---|---|
| 01 · Verify plan | HECHO | Brevo Account Usage: `Plan Free`, 300/300 daily marketing and transactional emails available, one user access | 0 EUR | 02 |
| 02 · Automation inventory | PARCIAL | Automation list visibly shows 7 flows: IDs 9, 8, 7, 5, 2, 1 active; ID 4 inactive | 0 EUR | Capture per-flow configuration without edits |
| 03 · Permanent registry in GitHub LAB | HECHO | Published through authenticated `CEREBRO · GitHub Universal` connector in branch `cerebro-engine-factory-v0`; no production changes | 0 EUR | Resume Work at Task 06; preserve evidence |
| 04 · Senders and resources | HECHO | Sender `Fénix Capital <hipotecas@fenixcapital.es>` verified; `fenixcapital.es` authenticated; Brevo reports sender domains comply with Google/Yahoo/Microsoft requirements; DMARC configured | 0 EUR | 05 / 06 |
| 05 · NEWS001 B2C draft | PARCIAL | Campaign draft **112** `NEWS001 · Newsletter Particulares · Noviembre 2026 · BORRADOR`; verified HTML preview with branded logo, image, responsive layout and editorial modules. List #17 has 0 recipients, so Brevo would not persist it as an audience. The HTML preview displayed the literal unsubscribe placeholder as an encoded Brevo URL, so it must be replaced with Brevo's own validated unsubscribe block before any send. | 0 EUR | Assign list #17 when it has a valid subscriber / approved test recipient and repair/verify unsubscribe in preview |
| 06 · NEWS001 B2B draft | PARCIAL | Campaign draft **113** `NEWS001 · Newsletter Inmobiliarias · Noviembre 2026 · BORRADOR` was created. Brevo campaign edit view remained on loading skeleton after creation and after one safe reload. | 0 EUR | Re-open ID 113; configure B2B subject, content, list #18, exclusion rule for Salinas |

## Verified plan boundary

- No paid plan, credits, SMS, WhatsApp, upgrade or billing change was accepted.
- Free plan shows 300 emails per day and 300 remaining at the time of verification.
- Lists #17 and #18 were observed as zero-recipient audiences in the campaign recipient chooser; therefore no campaign was scheduled or sent.

## Rollback

- B2C campaign 112 and B2B campaign 113 are drafts only. Neither was scheduled nor sent.
- Existing automations and existing campaigns were not paused, resumed, deleted, or edited.

## First pending task

Re-open Brevo campaign **113**, finish the B2B draft, then continue with Task 07 only after preserving this checkpoint in the GitHub LAB registry.
## Consolidation by CEREBRO ChatGPT (18 Nov 2026)
- Original checkpoint copied verbatim from the user's personal Library except task 03 updated to HECHO after this authenticated GitHub write.
- Fresh read-only Brevo list verification: #17 zero members, #18 zero members.
- Work verified 300/300 daily emails remaining **at its checkpoint**. Do not misrepresent as 300 used or imply current later quota.
- Draft IDs 112 B2C and 113 B2B are **Work-recorded**, not independently fetched via live Brevo campaign API in this ChatGPT session.
- Old automation #9 not paused; new automations not activated. No commercial emails sent by NEWS001.
- CEREBRO-generated canonical HTML: 10 blocks, 13 links, official logo+hero, passed LAB CI; native Brevo unsubscribe still needs an E2E test and approval.
- Future reports must not state NEWS001 AUTONOMOUS in PROD absent actual list→trigger→delivery and unsubscribe proof.

## Verificación incremental 18/11/2026, tras agotarse los créditos Work
- Datos de la última comunicación de Work, aportados por el propietario: campaña B2B #113 con diseño, asunto y preheader guardados; automatizaciones #10 y #11 creadas e inactivas, disparadores #17/#18; #10 enlazada a mensaje de automatización B2C #115, pero la plantilla necesita activación. Sin activar nada.
- Verificación directa mediante Opera read-only: #10 tiene acción `Enviar un email`, asunto B2C y disparador lista #17; figura INACTIVA. #11 tiene disparador de lista #18 y figura INACTIVA; **no tiene acción `Enviar un email` visible**, por lo que falta mensaje B2B.
- Verificación directa de Gmail propio autorizado: llegó una prueba B2C de Fénix el 18/11/2026 a las 12:32:59 UTC, asunto `TEST - La casa te gusta. Ahora hablemos de los números.`. El cuerpo incluye enlace real Brevo `/mk/un/v2/` de baja, pero NO se ha pulsado ni verificado el funcionamiento de la baja.
- ACCIÓN NUEVA (conector Brevo): contacto personal autorizado de prueba agregado correctamente a las listas #17 y #18, **un suscriptor de prueba en cada una**, Brevo respondió `success` y el `get_list` posterior confirmó ambos contadores a 1. No se importaron particulares históricos ni contactos comerciales ni Salinas.
- Se mantiene desactivado el envío comercial nuevo; #9 sigue activa, otras automatizaciones intactas. NO consta prueba de entrega B2B ni programación semanal autónoma ni circuito web/social completo.
- **Siguiente prioridad concreta:** completar acción de email de #11 y validar contenido/mensajes y baja; probar B2B con único buzón autorizado; probar consentimiento real end-to-end (sin inventarlo) antes de activar #10/#11; pausar #9 solo al certificar el relevo; configurar calendario editorial semanal vigente y envío respetando cuota.
