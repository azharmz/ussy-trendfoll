-- USSY TrendFoll — migrasi stop anchor ke Filled/Open H+1
-- Aman dijalankan ulang. Posisi closed tidak diubah.

alter table positions
    add column if not exists atr14_at_entry numeric;

-- Pulihkan ATR T0 dari aturan lama: stop = Trigger T0 - 2*ATR T0.
update positions
set atr14_at_entry = (entry_price - stop_price) / 2.0
where atr14_at_entry is null
  and stop_price is not null
  and entry_price > stop_price;

-- Terapkan aturan baru hanya pada posisi yang masih aktif dan sudah filled.
update positions
set stop_price = realistic_entry_price - 2.0 * atr14_at_entry,
    updated_at = now()
where status = 'active'
  and realistic_entry_price is not null
  and atr14_at_entry is not null
  and stop_price is distinct from realistic_entry_price - 2.0 * atr14_at_entry;
