create table if not exists public.cerebro_device_pairings_preprod (
  pairing_id uuid primary key default gen_random_uuid(),
  device_id text not null,
  company_id text not null,
  environment text not null check (environment in ('LAB','PREPROD')),
  version text not null,
  pair_code_sha256 text not null unique,
  expires_at timestamptz not null,
  used_at timestamptz null,
  created_at timestamptz not null default now()
);

alter table public.cerebro_device_pairings_preprod enable row level security;
revoke all on table public.cerebro_device_pairings_preprod from anon, authenticated;
grant select, insert, update, delete on table public.cerebro_device_pairings_preprod to service_role;

create index if not exists cerebro_device_pairings_preprod_device_idx
  on public.cerebro_device_pairings_preprod(device_id, company_id, environment, version, expires_at)
  where used_at is null;
