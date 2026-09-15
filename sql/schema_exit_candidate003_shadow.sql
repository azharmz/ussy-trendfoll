-- EXIT-CAND-003 non-decisioning shadow persistence
-- Contract is immutable: exit-cand-003-shadow-v1.
-- This table is observational and MUST NOT drive production position exits.

create table if not exists public.exit_candidate003_shadow (
    id bigint generated always as identity primary key,
    position_id bigint not null references public.positions(id),
    symbol text not null,
    contract_version text not null,
    signal_date date not null,
    shadow_entry_date date not null,
    shadow_entry_price numeric not null,
    atr14_t0 numeric not null,
    initial_stop numeric not null,
    operative_stop numeric not null,
    status text not null default 'active', -- active | exited | invariant_failure
    last_session_date date,
    days_observed integer not null default 0,
    hypothetical_exit_reason text,
    hypothetical_exit_date date,
    hypothetical_exit_price numeric,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(position_id, contract_version)
);

create index if not exists idx_exit_cand003_shadow_status
    on public.exit_candidate003_shadow(contract_version, status);
create index if not exists idx_exit_cand003_shadow_symbol
    on public.exit_candidate003_shadow(symbol);

alter table public.exit_candidate003_shadow enable row level security;
drop policy if exists "exit_candidate003_shadow read-only public" on public.exit_candidate003_shadow;
create policy "exit_candidate003_shadow read-only public"
    on public.exit_candidate003_shadow for select
    to anon, authenticated
    using (true);

-- Explicit grants are required by current Supabase Data API defaults.
grant select on table public.exit_candidate003_shadow to anon, authenticated;
grant select, insert, update, delete on table public.exit_candidate003_shadow to service_role;
grant usage, select on sequence public.exit_candidate003_shadow_id_seq to service_role;
