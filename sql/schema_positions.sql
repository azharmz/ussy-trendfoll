-- USSY TrendFoll — Tambahan schema untuk exit tracking
-- Jalankan setelah sql/schema.sql (tabel watchlist & sector_cache sudah ada).

create table if not exists positions (
    id bigint generated always as identity primary key,
    symbol text not null,
    entry_date date not null,
    entry_price numeric not null,          -- close hari sinyal (match backtest, apple-to-apple) -- "Trigger"
    realistic_entry_price numeric,          -- open hari BERIKUTNYA (realistis, terisi 1 hari setelah entry_date) -- "Entry"
    atr14_at_entry numeric,                 -- ATR14 hari sinyal T0; dipakai dengan filled H+1 untuk stop
    prev_close numeric,                     -- close T-1 (hari sebelum sinyal) -- untuk metrik T-1->T0 momentum
    max_close_since_entry numeric,          -- untuk hitung MFE (Maximum Favorable Excursion), basis close harian
    min_close_since_entry numeric,          -- untuk hitung MAE (Maximum Adverse Excursion), basis close harian
    mark_price numeric,                     -- harga terkini, di-update tiap run selama status='active'
    stop_price numeric not null,          -- realistic_entry_price - 2*ATR14 T0 (sementara Trigger-based sampai H+1)
    status text not null default 'active', -- active | stop_loss | trend_exit | max_holding
    exit_date date,
    exit_price numeric,
    days_held integer,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Cegah 2 posisi aktif bersamaan untuk symbol yang sama
create unique index if not exists idx_positions_active_symbol
    on positions (symbol)
    where status = 'active';

create index if not exists idx_positions_status on positions (status);

alter table positions enable row level security;

drop policy if exists "positions read-only public" on positions;
create policy "positions read-only public"
    on positions for select
    to anon, authenticated
    using (true);

-- service_role otomatis bypass RLS untuk insert/update dari GitHub Actions.

-- ============================================================
-- MIGRATION: kalau tabel `positions` sudah pernah dibuat sebelumnya
-- (versi tanpa realistic_entry_price), jalankan baris ini saja:
-- ============================================================
alter table positions add column if not exists realistic_entry_price numeric;
alter table positions add column if not exists atr14_at_entry numeric;
alter table positions add column if not exists mark_price numeric;
alter table positions add column if not exists prev_close numeric;
alter table positions add column if not exists max_close_since_entry numeric;
alter table positions add column if not exists min_close_since_entry numeric;


-- PROB-017 identity hardening.
-- Canonical immutable lifecycle identity is positions.id.
-- Under the current single-strategy production contract, one signal occurrence
-- per symbol/day is valid; replay/retry must reuse it rather than insert another.
-- Historical conflicts are preserved. This trigger blocks NEW duplicates without
-- destructively rewriting the existing audit trail.
create index if not exists idx_positions_symbol_entry_date
    on positions (symbol, entry_date);

create or replace function reject_duplicate_position_signal_identity()
returns trigger language plpgsql
set search_path = public
as $
begin
    if exists (
        select 1 from positions p
        where p.symbol = new.symbol and p.entry_date = new.entry_date
    ) then
        raise exception 'duplicate production position signal identity: (%, %)',
            new.symbol, new.entry_date;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_positions_reject_duplicate_signal_identity on positions;
create trigger trg_positions_reject_duplicate_signal_identity
before insert on positions
for each row execute function reject_duplicate_position_signal_identity();
