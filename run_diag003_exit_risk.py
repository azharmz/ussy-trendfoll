"""DIAG-003 observational audit of the current TrendFoll exit/risk contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

SAMPLE_SIZE = 100
ATR_MULT = 2.0
MAX_HOLD = 45
CHECKPOINTS = (5, 10, 20, 45)
EARLY = (1, 3, 5, 10)


def sample_ids(ready):
    p = ready[["security_id", "ticker"]].drop_duplicates().astype(str)
    p["rank"] = p.apply(lambda r: hashlib.sha256(f"{r.security_id}|{r.ticker}".encode()).hexdigest(), axis=1)
    return p.sort_values(["rank", "security_id"]).head(SAMPLE_SIZE)["security_id"].tolist()


def med(s):
    s = pd.Series(s).dropna()
    return None if s.empty else float(s.median())


def rate(s):
    s = pd.Series(s).dropna()
    return None if s.empty else float(s.astype(bool).mean())


def summarize(df):
    rr = df["realized_return"].dropna()
    return {
        "n": int(len(df)),
        "exit_reasons": {str(k): int(v) for k, v in df["exit_reason"].value_counts(dropna=False).items()},
        "realized_return_median": med(rr),
        "realized_positive_rate": None if rr.empty else float((rr > 0).mean()),
        "days_held_median": med(df["exit_day"]),
        "mfe_to_exit_median": med(df["mfe_to_exit"]),
        "mae_to_exit_median": med(df["mae_to_exit"]),
        "giveback_median": med(df["giveback_from_max_close"]),
    }


def path_row(g, event):
    g = g.sort_values("date").reset_index(drop=True)
    t0 = pd.Timestamp(event["t0_date"])
    ix = g.index[g["date"] == t0]
    if len(ix) != 1 or ix[0] + 1 >= len(g):
        return None
    i0 = int(ix[0]); entry_i = i0 + 1
    entry = g.iloc[entry_i]
    entry_px = float(entry["open_raw"])
    atr = float(g.iloc[i0]["atr14"]) if pd.notna(g.iloc[i0]["atr14"]) else np.nan
    if not np.isfinite(entry_px) or not np.isfinite(atr) or atr <= 0:
        return None
    stop = entry_px - ATR_MULT * atr
    fwd = g.iloc[entry_i: entry_i + MAX_HOLD].copy().reset_index(drop=True)
    if fwd.empty:
        return None

    exit_reason = "censored"; exit_day = np.nan; exit_px = np.nan
    first_ema20 = np.nan; first_stop = np.nan
    for j, r in fwd.iterrows():
        day = j + 1
        if pd.isna(first_stop) and float(r["low_raw"]) <= stop:
            first_stop = day
        if pd.isna(first_ema20) and pd.notna(r.get("ema20")) and float(r["close_raw"]) < float(r["ema20"]):
            first_ema20 = day
        if float(r["low_raw"]) <= stop:
            exit_reason, exit_day, exit_px = "stop_loss", day, stop; break
        # production counts trading dates strictly after T0; T+1 is day 1.
        if day >= MAX_HOLD:
            exit_reason, exit_day, exit_px = "max_holding", day, float(r["close_raw"]); break
        if pd.notna(r.get("ema20")) and float(r["close_raw"]) < float(r["ema20"]):
            exit_reason, exit_day, exit_px = "trend_exit", day, float(r["close_raw"]); break

    realized = (exit_px / entry_px - 1) if np.isfinite(exit_px) else np.nan
    experienced_n = int(exit_day) if np.isfinite(exit_day) else len(fwd)
    exp = fwd.iloc[:experienced_n].copy()
    # High/low excursions describe price-path opportunity/risk; realized exit
    # still reproduces production stop priority and fill.
    mfe_exit = float(exp["high_raw"].max() / entry_px - 1) if not exp.empty else np.nan
    mae_exit = float(exp["low_raw"].min() / entry_px - 1) if not exp.empty else np.nan
    max_close = float(max(entry_px, exp["close_raw"].max())) if not exp.empty else entry_px
    giveback = (exit_px / max_close - 1) if np.isfinite(exit_px) else np.nan

    out = {
        "symbol": event["symbol"], "t0_date": str(t0.date()), "entry_date": str(pd.Timestamp(entry["date"]).date()),
        "entry_price": entry_px, "atr14_t0": atr, "stop_price": stop,
        "forward_bars": int(len(fwd)), "exit_reason": exit_reason, "exit_day": exit_day,
        "exit_price": exit_px, "realized_return": realized,
        "mfe_to_exit": mfe_exit, "mae_to_exit": mae_exit, "giveback_from_max_close": giveback,
        "first_stop_day": first_stop, "first_ema20_loss_day": first_ema20,
        "mature_45": bool(len(fwd) >= 45),
    }
    for h in EARLY:
        if len(fwd) >= h:
            hh = fwd.iloc[:h]
            out[f"stop_within_{h}"] = bool((hh["low_raw"] <= stop).any())
            out[f"negative_close_{h}"] = bool(float(hh.iloc[-1]["close_raw"]) / entry_px - 1 < 0)
            out[f"ema20_loss_within_{h}"] = bool(((hh["close_raw"] < hh["ema20"]) & hh["ema20"].notna()).any())
        else:
            out[f"stop_within_{h}"] = out[f"negative_close_{h}"] = out[f"ema20_loss_within_{h}"] = np.nan
    for h in CHECKPOINTS:
        if len(fwd) >= h:
            hh = fwd.iloc[:h]
            out[f"mfe_{h}"] = float(hh["high_raw"].max() / entry_px - 1)
            out[f"mae_{h}"] = float(hh["low_raw"].min() / entry_px - 1)
        else:
            out[f"mfe_{h}"] = out[f"mae_{h}"] = np.nan
    if len(fwd) >= 45:
        h45 = fwd.iloc[:45]
        highs = h45["high_raw"].astype(float).to_numpy(); lows = h45["low_raw"].astype(float).to_numpy()
        out["time_to_mfe45"] = int(np.nanargmax(highs) + 1)
        out["time_to_mae45"] = int(np.nanargmin(lows) + 1)
        out["day45_return_no_early_exit"] = float(h45.iloc[-1]["close_raw"] / entry_px - 1)
        mfe45 = out["mfe_45"]
        for h in (5, 10, 20):
            out[f"fraction_mfe45_by_{h}"] = (out[f"mfe_{h}"] / mfe45) if mfe45 and mfe45 > 0 else np.nan
    else:
        out["time_to_mfe45"] = out["time_to_mae45"] = out["day45_return_no_early_exit"] = np.nan
        for h in (5, 10, 20): out[f"fraction_mfe45_by_{h}"] = np.nan
    return out


def main():
    ready, manifest = load_ready_dataset()
    ids = sample_ids(ready)
    end = manifest.get("snapshot_date") or str(pd.to_datetime(ready["date"]).max().date())
    hist, report = load_research_history(ids, evaluation_end=end, min_preroll_bars=500, ready=ready, ready_manifest=manifest)
    feat = build_research_feature_store(hist)["features"].sort_values(["symbol", "date"]).copy()
    dec = compute_decision_layer(compute_hard_filter(feat)).sort_values(["symbol", "date"]).copy()
    events = build_signal_path_events(dec)
    eligible = dec.loc[dec["research_eligible"].astype(bool), ["symbol", "date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events = events.merge(eligible, on=["symbol", "t0_date"], how="inner")
    groups = {s:g for s,g in dec.groupby("symbol", sort=False)}
    rows = []
    for _, e in events.iterrows():
        r = path_row(groups[e["symbol"]], e)
        if r is not None: rows.append(r)
    paths = pd.DataFrame(rows)
    mature45 = paths[paths["mature_45"]].copy()
    early = {}
    for h in EARLY:
        early[str(h)] = {
            "n": int(paths[f"stop_within_{h}"].notna().sum()),
            "stop_touch_rate": rate(paths[f"stop_within_{h}"]),
            "negative_close_rate": rate(paths[f"negative_close_{h}"]),
            "ema20_loss_rate": rate(paths[f"ema20_loss_within_{h}"]),
        }
    checkpoints = {str(h): {"mfe_median": med(paths[f"mfe_{h}"]), "mae_median": med(paths[f"mae_{h}"])} for h in CHECKPOINTS}
    summary = {
        "diagnostic":"DIAG-003", "status":"OBSERVATIONAL_ONLY_NO_PRODUCTION_CHANGE",
        "ready_snapshot_date": manifest.get("snapshot_date"), "sample_size": len(ids),
        "eligible_onsets": int(len(events)), "paths": int(len(paths)), "mature_45": int(len(mature45)),
        "current_rule": summarize(paths), "mature45_current_rule": summarize(mature45),
        "early_failure": early, "checkpoints": checkpoints,
        "mature45_path": {
            "time_to_mfe45_median": med(mature45["time_to_mfe45"]),
            "time_to_mae45_median": med(mature45["time_to_mae45"]),
            "fraction_mfe45_by_5_median": med(mature45["fraction_mfe45_by_5"]),
            "fraction_mfe45_by_10_median": med(mature45["fraction_mfe45_by_10"]),
            "fraction_mfe45_by_20_median": med(mature45["fraction_mfe45_by_20"]),
            "day45_return_no_early_exit_median": med(mature45["day45_return_no_early_exit"]),
            "day45_positive_rate": None if mature45.empty else float((mature45["day45_return_no_early_exit"] > 0).mean()),
            "current_realized_return_median_same_subset": med(mature45["realized_return"]),
            "current_positive_rate_same_subset": None if mature45.empty else float((mature45["realized_return"] > 0).mean()),
        },
        "governance": {"optimization":"none", "production_change":"none", "survivorship":"current readiness universe, not PIT"},
    }
    paths.to_csv("diag003_exit_risk_paths.csv", index=False)
    Path("diag003_exit_risk_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))

if __name__ == "__main__": main()
