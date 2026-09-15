-- EXIT-CAND-003 append-only operational evidence ledger
-- Contract: exit-cand-003-shadow-v1. Evidence only; never drives production exits.

create table if not exists public.exit_candidate003_shadow_sessions (
    id bigint generated always as identity primary key,
    position_id bigint not null references public.positions(id),
    shadow_id bigint not null references public.exit_candidate003_shadow(id),
    symbol text not null,
    session_date date not null,
    contract_version text not null,
    shadow_entry_date date not null,
    shadow_entry_price numeric not null,
    days_observed integer not null check (days_observed >= 1),
    open_raw numeric not null,
    high_raw numeric not null,
    low_raw numeric not null,
    close_raw numeric not null,
    ema20 numeric,
    operative_stop_before numeric not null,
    stop_source_before text not null,
    shadow_hh22 numeric,
    shadow_wilder_atr22 numeric,
    shadow_chandelier numeric,
    next_operative_stop numeric,
    hypothetical_exit_reason text,
    hypothetical_exit_price numeric,
    production_status text,
    production_exit_date date,
    production_exit_price numeric,
    gap_checked_first boolean not null default true,
    chandelier_arms_next_session boolean not null default true,
    created_at timestamptz not null default now(),
    unique(position_id, session_date, contract_version),
    check (high_raw >= low_raw),
    check (open_raw >= low_raw and open_raw <= high_raw),
    check (close_raw >= low_raw and close_raw <= high_raw),
    check (hypothetical_exit_reason is null or hypothetical_exit_price is not null)
);

create index if not exists idx_exit_cand003_shadow_sessions_symbol_date
    on public.exit_candidate003_shadow_sessions(symbol, session_date);
create index if not exists idx_exit_cand003_shadow_sessions_contract_date
    on public.exit_candidate003_shadow_sessions(contract_version, session_date);

alter table public.exit_candidate003_shadow_sessions enable row level security;

drop policy if exists "exit_candidate003_shadow_sessions read-only public"
    on public.exit_candidate003_shadow_sessions;
create policy "exit_candidate003_shadow_sessions read-only public"
    on public.exit_candidate003_shadow_sessions for select
    to anon, authenticated
    using (true);

-- Client roles can observe evidence but cannot mutate it. Backend shadow job writes
-- with the server-side service role / secret key only.
revoke insert, update, delete on table public.exit_candidate003_shadow_sessions from anon, authenticated;
grant select on table public.exit_candidate003_shadow_sessions to anon, authenticated;
grant select, insert on table public.exit_candidate003_shadow_sessions to service_role;
revoke update, delete on table public.exit_candidate003_shadow_sessions from service_role;
grant usage, select on sequence public.exit_candidate003_shadow_sessions_id_seq to service_role;
