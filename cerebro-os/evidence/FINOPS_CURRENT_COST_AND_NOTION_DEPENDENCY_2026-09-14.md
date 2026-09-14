# CEREBRO FinOps — current cost + Notion dependency evidence — 2026-09-14

## ESTADO

State: **PARCIAL / AUDITED / MONEY_LIMIT for billing changes**

This evidence records only costs confirmed by the owner or current connected-system evidence. Currencies are kept separate; no hidden FX conversion is applied.

## CONFIRMED CURRENT COSTS

EUR recurring/currently observed:
- Notion: `68.97 EUR/month` — owner-confirmed current bill, 2 users.
- Canva: `16.00 EUR/month`.
- Hostinger Business Email: `14.50 EUR/month`.
- Make: approximately `10.59 EUR/month`.
- Google Cloud `fenix-trading-lab`: currently observed `0.34 EUR` in Resource Manager; this is not treated as a stable monthly baseline without Billing-by-SKU evidence.

EUR subtotal using the values above: `110.40 EUR`, with the GCP `0.34 EUR` treated as currently observed rather than a guaranteed recurring monthly charge.

USD:
- Supabase: `25 USD/month`.

No combined EUR+USD total is asserted without an explicit FX conversion.

## NOTION DEPENDENCY AUDIT

The current Notion subscription cannot be removed blindly because active Make workflows depend on Notion API/modules. Confirmed active examples include:
- inbound messaging CORE / opportunity dedupe and registration;
- SEO GSC 30d → Notion inventory;
- social-network watchdog flows;
- CEREBRO signal → idea/evaluation/laboratory flow;
- LinkedIn / Instagram / Facebook analytics and reconciliation flows.

Connected Notion workspace tooling is operational. A workspace-agent search returned no shared agents at audit time.

Interpretation:
- CEREBRO has real **Notion API/data** dependencies.
- No current evidence proves that these dependencies require active Notion Agents.
- The current higher-cost plan is therefore a **strong downgrade candidate**, but not yet an approved billing action.

## GATE BEFORE DOWNGRADE

Before any plan change:
1. confirm no active workflow requires a Business-only capability rather than standard API/integration access;
2. preserve every existing Make/Notion contract;
3. snapshot affected database/data-source identifiers and integration permissions;
4. prepare a rollback/re-upgrade path;
5. only then request explicit owner action for the billing change (`MONEY_LIMIT`).

## SAFETY

- No subscription was changed.
- No Notion integration was disconnected.
- No Make scenario was deactivated.
- No payment method was modified.
- No new paid service was introduced.
