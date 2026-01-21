create table if not exists countries (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  iso_code char(2) not null unique,
  region text not null,
  population bigint,
  created_at timestamptz not null default now()
);

create table if not exists capitals (
  id uuid primary key default gen_random_uuid(),
  country_id uuid not null references countries(id) on delete cascade,
  name text not null,
  latitude numeric(9, 6) not null,
  longitude numeric(9, 6) not null,
  population bigint,
  timezone text,
  created_at timestamptz not null default now()
);

create table if not exists landmarks (
  id uuid primary key default gen_random_uuid(),
  capital_id uuid not null references capitals(id) on delete cascade,
  name text not null,
  type text not null,
  description text,
  created_at timestamptz not null default now()
);

create index if not exists capitals_country_id_idx on capitals(country_id);
create index if not exists landmarks_capital_id_idx on landmarks(capital_id);

insert into countries (name, iso_code, region, population)
values
  ('Argentina', 'AR', 'América del Sur', 46044703),
  ('España', 'ES', 'Europa', 48434560)
on conflict (iso_code) do nothing;

insert into capitals (country_id, name, latitude, longitude, population, timezone)
select id, 'Buenos Aires', -34.603684, -58.381559, 3120612, 'America/Argentina/Buenos_Aires'
from countries where iso_code = 'AR'
on conflict do nothing;

insert into capitals (country_id, name, latitude, longitude, population, timezone)
select id, 'Madrid', 40.416775, -3.703790, 3266126, 'Europe/Madrid'
from countries where iso_code = 'ES'
on conflict do nothing;

insert into landmarks (capital_id, name, type, description)
select capitals.id, 'Obelisco', 'Monumento', 'Icono urbano de Buenos Aires.'
from capitals where name = 'Buenos Aires'
on conflict do nothing;

insert into landmarks (capital_id, name, type, description)
select capitals.id, 'Puerta de Alcalá', 'Monumento', 'Monumento histórico en Madrid.'
from capitals where name = 'Madrid'
on conflict do nothing;
