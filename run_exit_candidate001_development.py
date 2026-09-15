"""Governed development evaluation for frozen EXIT-CAND-001 / 001B.

Representation is frozen in docs/EXIT_CANDIDATE_REPRESENTATION_001.md.
No parameter search is performed here.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_exit_iso001 as iso

OUT = Path("artifacts/exit_candidate001_development")
MAX_HOLD = 45
CHAND_PERIOD = 22
CHAND_ATR_MULT = 3.0
VARIANTS = ("CURRENT", "EXIT-CAND-001", "EXIT-CAND-001B")


def _true_range(g: pd.DataFrame) -> pd.Series:
    prev = g["close_raw"].shift(1)
    return pd.concat([
        g["high_raw"] - g["low_raw"],
        (g["high_raw"] - prev).abs(),
        (g["low_raw"] - prev).abs(),
    ], axis=1).max(axis=1)


def add_chandelier(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()
    # Wilder ATR22; candidate stop used on day t is based only on data through t-1.
    tr = _true_range(g)
    atr22 = tr.ewm(alpha=1 / CHAND_PERIOD, adjust=False, min_periods=CHAND_PERIOD).mean()
    hh22 = g["high_raw"].rolling(CHAND_PERIOD, min_periods=CHAND_PERIOD).max()
    g["chandelier_raw"] = hh22 - CHAND_ATR_MULT * atr22
    g["chandelier_prior"] = g["chandelier_raw"].shift(1)
    return g


def evaluate(g: pd.DataFrame, i0: int, variant: str):
    if i0 + MAX_HOLD >= len(g):
        return None
    entry_i = i0 + 1
    entry = float(g.iloc[entry_i]["open_raw"])
    atr0 = float(g.iloc[i0]["atr14"])
    if not np.isfinite(entry) or not np.isfinite(atr0) or atr0 <= 0:
        return None
    initial_stop = entry - 2.0 * atr0
    operative_stop = initial_stop
    highs, lows = [], []
    exit_i = i0 + MAX_HOLD
    exit_price = float(g.iloc[exit_i]["close_raw"])
    reason = "max_holding"

    for idx in range(entry_i, i0 + MAX_HOLD + 1):
        row = g.iloc[idx]
        day = idx - i0
        highs.append(float(row["high_raw"]))
        lows.append(float(row["low_raw"]))

        if variant == "CURRENT":
            stop_today = initial_stop
        else:
            prior_chand = float(row["chandelier_prior"]) if pd.notna(row["chandelier_prior"]) else np.nan
            if np.isfinite(prior_chand):
                operative_stop = max(operative_stop, prior_chand)
            stop_today = operative_stop

        if float(row["low_raw"]) <= stop_today:
            exit_i, exit_price = idx, stop_today
            reason = "stop_loss" if variant == "CURRENT" else "risk_stop"
            break
        if day >= MAX_HOLD:
            exit_i, exit_price, reason = idx, float(row["close_raw"]), "max_holding"
            break
        if variant in ("CURRENT", "EXIT-CAND-001"):
            ema20 = float(row["ema20"])
            if np.isfinite(ema20) and float(row["close_raw"]) < ema20:
                exit_i, exit_price, reason = idx, float(row["close_raw"]), "trend_exit"
                break

    ret = exit_price / entry - 1.0
    mfe = max(highs) / entry - 1.0
    mae = min(lows) / entry - 1.0
    return {
        "variant": variant,
        "entry_price": entry,
        "exit_price": exit_price,
        "realized_return": ret,
        "holding_days": exit_i - i0,
        "exit_reason": reason,
        "mfe_to_exit": mfe,
        "mae_to_exit": mae,
        "giveback": ret - mfe,
    }


def summarize(df: pd.DataFrame) -> dict:
    out = {}
    for variant, x in df.groupby("variant"):
        r = x["realized_return"]
        out[variant] = {
            "n": int(len(x)),
            "median_return": float(r.median()),
            "positive_rate": float((r > 0).mean()),
            "q25_return": float(r.quantile(.25)),
            "q75_return": float(r.quantile(.75)),
            "median_holding": float(x["holding_days"].median()),
            "median_mfe": float(x["mfe_to_exit"].median()),
            "median_mae": float(x["mae_to_exit"].median()),
            "median_giveback": float(x["giveback"].median()),
            "exit_reasons": {str(k): int(v) for k, v in x["exit_reason"].value_counts().items()},
        }
    current = df[df.variant == "CURRENT"].set_index("event_id")["realized_return"]
    for variant in VARIANTS[1:]:
        x = df[df.variant == variant].set_index("event_id")["realized_return"]
        d = x - current
        out[variant]["median_return_difference_vs_current"] = out[variant]["median_return"] - out["CURRENT"]["median_return"]
        out[variant]["paired_event_delta_median_vs_current"] = float(d.median())
        out[variant]["improved_fraction"] = float((d > 1e-12).mean())
        out[variant]["worsened_fraction"] = float((d < -1e-12).mean())
        out[variant]["unchanged_fraction"] = float((d.abs() <= 1e-12).mean())
    return out


def main():
    # Reuse the exact governed corpus builder from EXIT-ISO-001.
    features, events, meta = iso.build_corpus()
    features = features.sort_values(["security_id", "date"]).copy()
    groups = {sid: add_chandelier(g.reset_index(drop=True)) for sid, g in features.groupby("security_id", sort=False)}
    rows = []
    for event_id, e in events.reset_index(drop=True).iterrows():
        sid = e["security_id"]
        g = groups.get(sid)
        if g is None:
            continue
        ix = np.flatnonzero(pd.to_datetime(g["date"]).dt.normalize().values == pd.Timestamp(e["date"]).normalize().to_datetime64())
        if len(ix) != 1:
            continue
        i0 = int(ix[0])
        # Exact 45-bar comparable corpus for all variants.
        if i0 + MAX_HOLD >= len(g):
            continue
        candidate = []
        for variant in VARIANTS:
            z = evaluate(g, i0, variant)
            if z is None:
                candidate = []
                break
            z.update({"event_id": int(event_id), "security_id": sid, "ticker": e.get("ticker"), "t0": str(pd.Timestamp(e["date"]).date())})
            candidate.append(z)
        rows.extend(candidate)

    df = pd.DataFrame(rows)
    counts = df.groupby("variant").size().to_dict()
    if not counts or len(set(counts.values())) != 1 or set(counts) != set(VARIANTS):
        raise RuntimeError(f"non-comparable candidate corpus: {counts}")
    summary = {
        "status": "DEVELOPMENT_ONLY_NOT_VALIDATION",
        "representation": {"chandelier_period": 22, "chandelier_atr_multiplier": 3.0, "lookahead_guard": "day-t stop uses Chandelier through t-1", "initial_stop": "entry - 2*ATR14(T0)", "max_observation_days": 45},
        "corpus": meta,
        "variants": summarize(df),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "events.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
