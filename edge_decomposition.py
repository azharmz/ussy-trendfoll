"""Governed TrendFoll edge-decomposition helpers. Observational only."""
from __future__ import annotations
import numpy as np
import pandas as pd

def _ret(end, start):
    if pd.isna(end) or pd.isna(start) or float(start) == 0:
        return np.nan
    return float(end) / float(start) - 1.0

def _entry_ready(df):
    return (df["hard_filter_status"].eq("PASS") & df["has_breakout"].fillna(False).astype(bool)
            & df["has_volume_confirmation"].fillna(False).astype(bool))

def build_edge_events(decided):
    required={"symbol","date","open_raw","high_raw","low_raw","close_raw","hard_filter_status",
              "has_breakout","has_volume_confirmation","prev_pivot_high","atr14"}
    missing=sorted(required-set(decided.columns))
    if missing: raise ValueError(f"edge decomposition missing required columns: {missing}")
    df=decided.copy(); df["date"]=pd.to_datetime(df["date"]).dt.normalize()
    df=df.sort_values(["symbol","date"]).reset_index(drop=True)
    if df.duplicated(["symbol","date"],keep=False).any():
        raise ValueError("edge decomposition requires unique symbol+date rows")
    df["_ready"]=_entry_ready(df)
    prior=df.groupby("symbol")["_ready"].shift(1).fillna(False).astype(bool)
    df["_onset"]=df["_ready"] & ~prior
    out=[]
    for symbol,rows in df.groupby("symbol",sort=False):
        rows=rows.reset_index(drop=True)
        for pos in rows.index[rows["_onset"]]:
            t0=rows.iloc[pos]; pivot=t0["prev_pivot_high"]
            if pd.isna(pivot): continue
            fut={n:(rows.iloc[pos+n] if pos+n<len(rows) else None) for n in range(1,11)}
            t1=fut[1]
            if t1 is None: continue
            t1open=t1["open_raw"]; t1close=t1["close_raw"]; t1low=t1["low_raw"]
            accepted=bool(pd.notna(t1close) and float(t1close)>=float(pivot))
            rejected=bool(pd.notna(t1close) and float(t1close)<float(pivot))
            retest=bool(accepted and pd.notna(t1low) and float(t1low)<=float(pivot))
            stayed=bool(accepted and pd.notna(t1low) and float(t1low)>float(pivot))
            e={"symbol":symbol,"t0_date":t0["date"],"pivot":float(pivot),"atr14_t0":t0["atr14"],
               "t0_close":t0["close_raw"],"t1_date":t1["date"],"t1_open":t1open,"t1_close":t1close,
               "t1_low":t1low,"gap_t0close_t1open":_ret(t1open,t0["close_raw"]),
               "t1_accepted":accepted,"t1_rejected":rejected,"t1_retest_held":retest,
               "t1_stayed_above":stayed}
            for h in (1,3,5,10):
                b=fut[h]
                e[f"ret_t1open_t{h}close"]=_ret(b["close_raw"],t1open) if b is not None else np.nan
                path=[fut[n] for n in range(1,h+1) if fut[n] is not None]
                if len(path)==h and pd.notna(t1open) and float(t1open)!=0:
                    e[f"mfe_t1_h{h}"]=max(float(x["high_raw"]) for x in path)/float(t1open)-1
                    e[f"mae_t1_h{h}"]=min(float(x["low_raw"]) for x in path)/float(t1open)-1
                    e[f"pivot_breakdown_close_by_{h}"]=any(float(x["close_raw"])<float(pivot) for x in path if pd.notna(x["close_raw"]))
                else:
                    e[f"mfe_t1_h{h}"]=np.nan; e[f"mae_t1_h{h}"]=np.nan; e[f"pivot_breakdown_close_by_{h}"]=np.nan
            t2=fut[2]
            if t2 is not None:
                t2open=t2["open_raw"]; e["t2_open"]=t2open
                for h in (5,10):
                    b=fut[h]; e[f"ret_t2open_t{h}close"]=_ret(b["close_raw"],t2open) if b is not None else np.nan
                    path=[fut[n] for n in range(2,h+1) if fut[n] is not None]
                    if len(path)==h-1 and pd.notna(t2open) and float(t2open)!=0:
                        e[f"mfe_t2_h{h}"]=max(float(x["high_raw"]) for x in path)/float(t2open)-1
                        e[f"mae_t2_h{h}"]=min(float(x["low_raw"]) for x in path)/float(t2open)-1
                    else:
                        e[f"mfe_t2_h{h}"]=np.nan; e[f"mae_t2_h{h}"]=np.nan
            out.append(e)
    return pd.DataFrame(out)

def summarize(events):
    def gs(g):
        def med(c):
            x=g[c].dropna() if c in g else pd.Series(dtype=float)
            return None if x.empty else float(x.median())
        return {"n":int(len(g)),"t5_mature":int(g["ret_t1open_t5close"].notna().sum()),
                "t10_mature":int(g["ret_t1open_t10close"].notna().sum()),
                "t1_t5_median":med("ret_t1open_t5close"),"t1_t10_median":med("ret_t1open_t10close"),
                "mfe10_median":med("mfe_t1_h10"),"mae10_median":med("mae_t1_h10"),
                "t2_t5_median":med("ret_t2open_t5close"),"t2_t10_median":med("ret_t2open_t10close")}
    groups={"all":events}
    for c in ("t1_accepted","t1_rejected","t1_retest_held","t1_stayed_above"):
        groups[c]=events.loc[events[c].fillna(False).astype(bool)]
    return {"diagnostic":"EDGE-DECOMPOSITION","status":"OBSERVATIONAL_ONLY","events":int(len(events)),
            "groups":{k:gs(v) for k,v in groups.items()},
            "breakdown_rates":{f"by_{h}":(None if events[f"pivot_breakdown_close_by_{h}"].dropna().empty else
                float(events[f"pivot_breakdown_close_by_{h}"].dropna().astype(bool).mean())) for h in (1,3,5,10)},
            "governance":"No entry/exit/filter/alert change authorized; T+2 views are causal diagnostics only."}
