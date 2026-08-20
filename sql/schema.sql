-- USSY TrendFoll — Supabase Schema
-- Project: https://rggtylvlrzzesrtumqzj.supabase.co
-- Jalankan di SQL Editor Supabase. Aman dijalankan ulang (idempotent).

-- ============================================================
-- 1. sector_cache — cache mapping sector, refresh cuma kalau basi (>30 hari)
-- ============================================================
create table if not exists sector_cache (
    symbol text primary key,
    sector text,
    industry text,
    sector_benchmark text,
    updated_at timestamptz not null default now()
);

-- ============================================================
-- 2. watchlist — output harian decision layer
-- ============================================================
create table if not exists watchlist (
    id bigint generated always as identity primary key,
    symbol text not null,
    date date not null,
    close_raw numeric,
    investability_status text not null,
    tradability_status text not null,
    has_breakout boolean,
    has_volume_confirmation boolean,
    has_tight_structure boolean,
    regime_status text,
    market_regime text,
    explanation_text text,
    created_at timestamptz not null default now(),
    unique (symbol, date)
);

create index if not exists idx_watchlist_date on watchlist (date desc);
create index if not exists idx_watchlist_investability on watchlist (investability_status);

-- ============================================================
-- 3. RLS — read-only untuk anon/authenticated (dipakai frontend web),
--    write cuma lewat service_role key (dipakai GitHub Actions)
-- ============================================================
alter table sector_cache enable row level security;
alter table watchlist enable row level security;

drop policy if exists "sector_cache read-only public" on sector_cache;
create policy "sector_cache read-only public"
    on sector_cache for select
    to anon, authenticated
    using (true);

drop policy if exists "watchlist read-only public" on watchlist;
create policy "watchlist read-only public"
    on watchlist for select
    to anon, authenticated
    using (true);

-- service_role otomatis bypass RLS, tidak perlu policy insert/update terpisah.
