# APP Gateway authenticated write cleanup rehearsal — 2026-09-14

## ESTADO

State: **CLEANUP_STRATEGY_GREEN / HTTP_WRITE_E2E_STILL_HIGH_RISK_GATED**

## HECHO

A live-schema, non-persistent cleanup rehearsal was executed inside explicit `BEGIN ... ROLLBACK` transactions. No test mutation persisted.

### Contact + expediente + firma

The rehearsal:
1. created a unique contact through `fenix_prod_contact_create_server` using the permanent CEREBRO operational actor;
2. deleted the exact returned contact record and asserted one-row cleanup;
3. created a unique expediente through `fenix_prod_exp_create_server` with a unique `example.invalid` email;
4. captured the returned expediente and generated client identifiers;
5. created a firma for that generated expediente through `fenix_prod_sign_create_server`;
6. deleted the exact generated firma;
7. deleted the exact generated expediente;
8. deleted the exact generated client;
9. asserted that none of those generated identifiers remained;
10. issued `ROLLBACK`.

Result returned by the transaction harness:
`CLEANUP_REHEARSAL_GREEN_ROLLED_BACK`.

### Notification state

Because `restore` clears dismissal but intentionally does not make a notification unread again, exact cleanup cannot rely on the public `restore` action alone.

The rehearsal therefore proved an exact-state strategy:
1. choose an authorized task;
2. snapshot whether `notification_state` exists plus its prior `read_at`, `dismissed_at`, `updated_at` values;
3. call `fenix_prod_notification_mark_server(..., 'dismiss')`;
4. restore the exact prior row, or delete the newly created row if none existed before;
5. assert state equality / absence as appropriate;
6. issue `ROLLBACK`.

Result returned by the transaction harness:
`NOTIFICATION_CLEANUP_REHEARSAL_GREEN_ROLLED_BACK`.

## SCHEMA EVIDENCE

Foreign-key inspection confirms relevant cleanup behavior, including:
- `expediente_personas -> expedientes`: `ON DELETE CASCADE`;
- `expediente_personas -> clientes`: `ON DELETE CASCADE`;
- `notification_state -> tareas`: `ON DELETE CASCADE`;
- `notification_state -> actors`: `ON DELETE CASCADE`;
- dependent expediente tables such as documents/tasks/offers/bank sends may use `NO ACTION`, therefore every real E2E cleanup must first assert that the newly-created expediente has no unexpected dependents before deletion.

## WHAT THIS PROVES

- Database cleanup strategies for all four write families are now proven without persisting test data.
- The canonical E2E plan can move from `cleanup missing` to `cleanup strategy proven`.

## WHAT THIS DOES NOT PROVE

- It does not execute the final browser/session -> Edge Gateway HTTP writes.
- Those final writes remain `HUMAN_REQUIRED(HIGH_RISK)` and require the authenticated session plus immediate capture of returned identifiers and cleanup according to this proven strategy.
- The permanent `CEREBRO-OPS-01` identity must never be deleted or retired as cleanup.

## SAFETY

- No password/token/secret was used in documentation.
- No persistent PROD test row remained from these rehearsals.
- No legacy RPC grant was revoked.
- No App/CRM contract was modified.
