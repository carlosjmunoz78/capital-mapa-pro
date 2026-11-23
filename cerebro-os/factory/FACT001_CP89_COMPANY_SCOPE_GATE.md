# CP89 · FACT-001 company scope gate · LAB

## HECHO
Se añade un gate ejecutable fail-closed sobre la rama CP88, sin tocar Worker, D1, secretos, cron, UMS, App/CRM, PROD ni main.

Fuentes vivas consumidas por el test:
- `cerebro-os/config/improvement_companies.lab.json`: Fenix Capital = `company_id=fenix`.
- `cerebro-os/registry/instances/SUP-001_FACT001-P5_CP88.lab.json`: instancia CP88 = `company_id=fenix-capital`, `registration_method=ADMIN_READONLY_EVIDENCE_SEED`.

## Resultado contractual
- `fenix` vs `fenix-capital` => `HOLD_COMPANY_ID_MISMATCH`.
- No se asume alias.
- No se atribuye la actividad P5 a la identidad canónica `fenix`.
- No se concede IAM.
- No se despacha UMS.
- Incluso con igualdad exacta de company_id, un registro administrativo CP88 no se convierte en aprovisionamiento FACT: `HOLD_NOT_FACTORY_PROVISIONED`.

## Rollback
Eliminar esta rama/PR. No existe cambio remoto de runtime que revertir.

## Next gate
1. Encontrar contrato firmado/verificable que autorice la correspondencia de identidad, si existe.
2. Encontrar emisor empresarial legítimo de `FACT.INVENTORY.READ` para JARVIS LAB, principal exclusivo, solo lectura y <=15 min.
3. Solo después ejecutar canario privado real JARVIS → FACT y correlacionar recibos.

Coste adicional contratado: 0 €. Estado: PARCIAL / FAIL-CLOSED CORRECTO.
