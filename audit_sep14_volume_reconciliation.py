"""Research-only FSE-015 diagnostic: test whether the historically suspicious
2026-09-14 R2 READY volume bar was reconciled after later READY publication.

No production/R2/Supabase mutation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from r2_ready import load_ready_dataset

TARGET_DATE = pd.Timestamp("2026-09-14")
OUT = Path("audit_artifacts/sep14_volume_reconciliation")
OUT.mkdir(parents=True, exist_ok=True)


def _safe_median(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.median()) if len(s) else np.nan


def main() -> None:
    df, manifest = load_ready_dataset()
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df.sort_values(["security_id", "date"])

    rows = []
    for sid, s in df.groupby("security_id", sort=False):
        s = s.sort_values("date").reset_index(drop=True)
        hit = s.index[s["date"] == TARGET_DATE]
        if len(hit) == 0:
            continue
        pos = int(hit[-1])
        if pos < 1:
            continue

        r = s.iloc[pos]
        prev = s.iloc[pos - 1]
        future = s.iloc[pos + 1] if pos + 1 < len(s) else None
        prior50 = s.iloc[max(0, pos - 50):pos]["volume"].dropna()
        current = float(r["volume"])
        prevvol = float(prev["volume"]) if pd.notna(prev["volume"]) else np.nan
        median50 = _safe_median(prior50)

        rows.append({
            "security_id": sid,
            "ticker": r["ticker"],
            "target_date": str(TARGET_DATE.date()),
            "target_volume": current,
            "prev_date": str(pd.Timestamp(prev["date"]).date()),
            "prev_volume": prevvol,
            "next_date": str(pd.Timestamp(future["date"]).date()) if future is not None else None,
            "next_volume": float(future["volume"]) if future is not None and pd.notna(future["volume"]) else np.nan,
            "median_prior50_volume": median50,
            "target_to_prev": current / prevvol if prevvol > 0 else np.nan,
            "target_to_prior50_median": current / median50 if median50 > 0 else np.nan,
            "target_is_prior50_min": bool(len(prior50) and current < prior50.min()),
        })

    out = pd.DataFrame(rows)
    ratio = out["target_to_prior50_median"] if len(out) else pd.Series(dtype=float)
    summary = {
        "manifest_snapshot_date": manifest.get("snapshot_date"),
        "ready_latest_market_date": str(pd.Timestamp(df["date"].max()).date()),
        "target_date": str(TARGET_DATE.date()),
        "target_rows_analyzed": int(len(out)),
        "target_below_all_prior50": int(out["target_is_prior50_min"].sum()) if len(out) else 0,
        "target_below_all_prior50_pct": float(out["target_is_prior50_min"].mean() * 100) if len(out) else np.nan,
        "target_to_prev_median": float(out["target_to_prev"].median()) if len(out) else np.nan,
        "target_to_prior50_median_cross_section_median": float(ratio.median()) if len(out) else np.nan,
        "target_to_prior50_median_p25": float(ratio.quantile(.25)) if len(out) else np.nan,
        "target_to_prior50_median_p75": float(ratio.quantile(.75)) if len(out) else np.nan,
        "count_target_lt_25pct_prior50_median": int((ratio < .25).sum()) if len(out) else 0,
        "count_target_lt_50pct_prior50_median": int((ratio < .50).sum()) if len(out) else 0,
        "reference_original_sep14_below_all_prior50": 933,
        "reference_original_sep14_below_all_prior50_pct": 76.28781684382666,
        "reference_original_sep14_to_prev_median": 0.16285281134103685,
        "reference_original_sep14_to_prior50_median": 0.15203372149958486,
        "reference_original_sep14_lt25pct": 875,
        "reference_original_sep14_lt50pct": 1025,
    }

    out.to_csv(OUT / "sep14_volume_reconciliation.csv", index=False)
    (OUT / "sep14_volume_reconciliation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
