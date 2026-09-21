# CEREBRO Browser Transport PREPROD V1.4

## Existing transport reused

The PREPROD Supabase project already contained:
- `cerebro_device_agents_preprod`
- `cerebro_device_nonces_preprod`
- `cerebro_device_commands_preprod`
- `cerebro_device_results_preprod`
- Edge Function `cerebro-device-gateway-preprod`

V1.4 reuses that transport instead of creating a second remote queue.

## V1.4 changes

- adds one-time, expiring pairing records storing only SHA-256 of the pairing code;
- device generates its long-lived bearer token locally;
- server stores only the bearer token SHA-256;
- token is protected on Windows with user-scoped DPAPI;
- gateway command delivery is constrained to exact `device_id + company_id + environment + version`;
- result submission is constrained to the same scope;
- outbound polling only: no inbound Internet port is opened on the PC;
- remote actuation remains LAB-only and currently accepts only `OPEN_LOCAL_TEST_PAGE`;
- PROD remains denied.

## Scope

Physical pilot:
- company_id: `fenix`
- environment: `LAB`
- version: `v0`
- device_id: `desktop-b0d4e7b9-1bde-46e5-8c99-b0f530214333`

The one-time pairing secret is not committed to the repository.
