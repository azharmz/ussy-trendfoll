"""Research-only diagnostic for suspicious latest-session R2 volume completeness.

No production/R2/Supabase mutation. Triggered after workflow registration.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from r2_ready import load_ready_dataset

OUT = Path("audit_artifacts/latest_volume_completeness")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    df, manifest = load_ready_dataset()
    df = df.copy().sort_values(["security_id", "date"])
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    latest_date = pd.Timestamp(df["date"].max())
    rows=[]
    for sid, s in df.groupby("security_id", sort=False):
        s=s.sort_values("date")
        cur=s[s["date"]==latest_date]
        if cur.empty: continue
        i=cur.index[-1]
        pos=s.index.get_loc(i)
        if pos < 1: continue
        prev=s.iloc[pos-1]
        r=cur.iloc[-1]
        trailing_prev=s.iloc[max(0,pos-50):pos]["volume"].dropna()
        current=float(r["volume"])
        prevvol=float(prev["volume"]) if pd.notna(prev["volume"]) else np.nan
        median_prev=float(trailing_prev.median()) if len(trailing_prev) else np.nan
        rows.append({
            "security_id":sid,"ticker":r["ticker"],"date":r["date"],
            "current_volume":current,"prev_date":prev["date"],"prev_volume":prevvol,
            "median_prior50_volume":median_prev,
            "current_to_prev": current/prevvol if prevvol>0 else np.nan,
            "current_to_prior50_median": current/median_prev if median_prev>0 else np.nan,
            "current_is_prior50_min": bool(len(trailing_prev) and current < trailing_prev.min()),
        })
    out=pd.DataFrame(rows)
    summary={
        "manifest_snapshot_date":manifest.get("snapshot_date"),
        "latest_market_date":str(latest_date.date()),
        "latest_rows_analyzed":int(len(out)),
        "current_below_all_prior50":int(out["current_is_prior50_min"].sum()),
        "current_below_all_prior50_pct":float(out["current_is_prior50_min"].mean()*100),
        "current_to_prev_median":float(out["current_to_prev"].median()),
        "current_to_prior50_median_cross_section_median":float(out["current_to_prior50_median"].median()),
        "current_to_prior50_median_p25":float(out["current_to_prior50_median"].quantile(.25)),
        "current_to_prior50_median_p75":float(out["current_to_prior50_median"].quantile(.75)),
        "count_current_lt_25pct_prior50_median":int((out["current_to_prior50_median"]<.25).sum()),
        "count_current_lt_50pct_prior50_median":int((out["current_to_prior50_median"]<.50).sum()),
    }
    out.to_csv(OUT/"latest_volume_completeness.csv",index=False)
    (OUT/"latest_volume_completeness_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
