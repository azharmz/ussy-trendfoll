-- PROB-003/004 persistent alert event + delivery ledger.
create table if not exists public.alert_events (
  id bigint generated always as identity primary key,
  event_key text not null unique,
  contract_version text not null,
  symbol text not null,
  effective_date date not null,
  transition_type text not null,
  from_state text not null,
  to_state text not null,
  source_previous_date date,
  payload jsonb not null,
  created_at timestamptz not null default now()
);
create table if not exists public.alert_deliveries (
  id bigint generated always as identity primary key,
  event_id bigint not null references public.alert_events(id) on delete restrict,
  transport text not null,
  status text not null check (status in ('pending','sending','failed','delivered')),
  claim_token uuid,
  claimed_at timestamptz,
  delivered_at timestamptz,
  external_message_id text,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(event_id,transport)
);
create table if not exists public.alert_delivery_attempts (
  id bigint generated always as identity primary key,
  attempt_id uuid not null unique,
  delivery_id bigint not null references public.alert_deliveries(id) on delete restrict,
  event_id bigint not null references public.alert_events(id) on delete restrict,
  transport text not null,
  status text not null check (status in ('attempted','failed','delivered')),
  attempted_at timestamptz not null default now(),
  finished_at timestamptz,
  external_message_id text,
  error text
);
create index if not exists idx_alert_events_effective on public.alert_events(effective_date desc,symbol);
create index if not exists idx_alert_deliveries_status on public.alert_deliveries(status,claimed_at);
create index if not exists idx_alert_attempts_event on public.alert_delivery_attempts(event_id,attempted_at desc);
alter table public.alert_events enable row level security;
alter table public.alert_deliveries enable row level security;
alter table public.alert_delivery_attempts enable row level security;
revoke all on public.alert_events from anon, authenticated;
revoke all on public.alert_deliveries from anon, authenticated;
revoke all on public.alert_delivery_attempts from anon, authenticated;
revoke all on public.alert_events from service_role;
revoke all on public.alert_deliveries from service_role;
revoke all on public.alert_delivery_attempts from service_role;
grant select,insert,update on public.alert_events to service_role;
grant select,insert,update on public.alert_deliveries to service_role;
grant select,insert,update on public.alert_delivery_attempts to service_role;
grant usage,select on sequence public.alert_events_id_seq to service_role;
grant usage,select on sequence public.alert_deliveries_id_seq to service_role;
grant usage,select on sequence public.alert_delivery_attempts_id_seq to service_role;

drop policy if exists "alert_events service only" on public.alert_events;
create policy "alert_events service only" on public.alert_events for all to service_role using (true) with check (true);
drop policy if exists "alert_deliveries service only" on public.alert_deliveries;
create policy "alert_deliveries service only" on public.alert_deliveries for all to service_role using (true) with check (true);
drop policy if exists "alert_delivery_attempts service only" on public.alert_delivery_attempts;
create policy "alert_delivery_attempts service only" on public.alert_delivery_attempts for all to service_role using (true) with check (true);
