"""
USSY TrendFoll — Telegram Notification
=========================================
Kirim ringkasan watchlist harian + alert exit posisi ke Telegram. Kalau
TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum di-set, skip diam-diam (tidak
error) — pola yang sama dipakai di USSY Signal (notify.py).
"""

import os
import requests
import pandas as pd

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LEN = 3800  # batas Telegram 4096 char, sisakan margin


def send_watchlist_summary(decision_df: pd.DataFrame, as_of_date):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[notify] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID belum di-set — skip notifikasi.")
        return

    text = _build_message(decision_df, as_of_date)
    for chunk in _split_message(text):
        _send(token, chat_id, chunk)


def send_exit_alerts(exits: list):
    """exits: list dict dari positions.check_exits() — kirim 1 pesan per exit,
    supaya jelas beda dari ringkasan watchlist harian."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id or not exits:
        return

    reason_label = {
        "stop_loss": "🔴 STOP LOSS",
        "trend_exit": "🟠 TREND PATAH",
        "max_holding": "🔵 MAX HOLDING (45 hari)",
    }

    for e in exits:
        label = reason_label.get(e["exit_reason"], e["exit_reason"])
        text = (
            f"{label} — {e['symbol']}\n\n"
            f"Trigger: ${e['trigger_price']:.2f}\n"
            f"Entry: ${e['entry_price']:.2f}\n"
            f"Exit: ${e['exit_price']:.2f}\n"
            f"PnL: {e['pnl_pct']:+.1f}%\n"
            f"Hari ditahan: {e['days_held']} hari bursa\n\n"
            f"Saatnya keluar dari posisi ini."
        )
        _send(token, chat_id, text)


def _build_message(decision_df: pd.DataFrame, as_of_date) -> str:
    date_str = pd.Timestamp(as_of_date).date().isoformat()

    if decision_df.empty:
        return f"📋 USSY TrendFoll — {date_str}\n\nTidak ada kandidat investability >= NEAR_PASS hari ini."

    n_total = len(decision_df)
    breakout = decision_df[decision_df["tradability_status"].isin(["PASS", "NEAR_PASS"])]
    pass_full = decision_df[
        (decision_df["investability_status"] == "PASS") & (decision_df["tradability_status"] == "PASS")
    ]

    lines = [
        f"📋 USSY TrendFoll — {date_str}",
        "",
        f"{n_total} kandidat investability >= NEAR_PASS, {len(breakout)} dengan sinyal breakout hari ini.",
        "",
    ]

    if not pass_full.empty:
        lines.append("🟢 PASS penuh (Investability + Tradability):")
        for _, r in pass_full.iterrows():
            lines.append(f"  • {r['symbol']} — ${r['close_raw']:.2f}")
        lines.append("")

    breakout_only = breakout[~breakout["symbol"].isin(pass_full["symbol"])]
    if not breakout_only.empty:
        lines.append("🟡 Ada breakout, belum PASS penuh:")
        for _, r in breakout_only.iterrows():
            lines.append(f"  • {r['symbol']} — ${r['close_raw']:.2f} (tradability: {r['tradability_status']})")
        lines.append("")

    lines.append("Detail lengkap: cek dashboard web.")
    return "\n".join(lines)


def _split_message(text: str):
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_MESSAGE_LEN:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def _send(token: str, chat_id: str, text: str):
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"[notify] Gagal kirim Telegram: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[notify] Error kirim Telegram: {type(e).__name__}: {e}")
