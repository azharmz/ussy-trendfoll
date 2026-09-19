"""EDGE-ECON-001: frozen combined entry/exit economic conversion."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import run_exit_candidate003_validation as val
import run_exit_candidate003_development as ex
from edge_decomposition import build_edge_events

OUT=Path("artifacts/edge_econ001")
COSTS=(0,5,10,20)

def eval_t2(g,e,variant):
    g=g.sort_values("date").reset_index(drop=True); t0=pd.Timestamp(e["t0_date"]); ix=g.index[g.date==t0]
    if len(ix)!=1: return None
    i0=int(ix[0]); t1=i0+1; entry_i=i0+2
    if entry_i+ex.MAX_HOLD-1>=len(g): return None
    pivot=float(e["pivot"])
    if float(g.iloc[t1].close_raw)<pivot: return None
    entry=float(g.iloc[entry_i].open_raw); atr0=float(g.iloc[i0].atr14) if pd.notna(g.iloc[i0].atr14) else np.nan
    if not np.isfinite(entry) or not np.isfinite(atr0) or atr0<=0:return None
    initial=entry-2*atr0; operative=initial
    fwd=g.iloc[entry_i:entry_i+ex.MAX_HOLD].reset_index(drop=True)
    reason="max_holding" if variant=="CURRENT-ACCEPTED" else "observation_boundary"
    exit_day=ex.MAX_HOLD; exit_price=float(fwd.iloc[-1].close_raw); prev=None
    for j,row in fwd.iterrows():
        day=j+1; stop=initial if variant=="CURRENT-ACCEPTED" else operative
        op=float(row.open_raw); lo=float(row.low_raw); hi=float(row.high_raw)
        if variant!="CURRENT-ACCEPTED" and prev is not None and stop<prev-ex.TOL: raise RuntimeError("stop decreased")
        prev=stop
        if variant=="CURRENT-ACCEPTED":
            if lo<=stop: reason="stop_loss"; exit_day=day; exit_price=stop; break
        else:
            if op<=stop: reason="risk_stop_gap"; exit_day=day; exit_price=op; break
            if lo<=stop:
                if stop<lo-ex.TOL or stop>hi+ex.TOL: raise RuntimeError("touch outside range")
                reason="risk_stop_touch"; exit_day=day; exit_price=stop; break
        if day>=ex.MAX_HOLD: break
        if pd.notna(row.ema20) and float(row.close_raw)<float(row.ema20):
            reason="trend_exit"; exit_day=day; exit_price=float(row.close_raw); break
        if variant!="CURRENT-ACCEPTED":
            chand=float(row.chandelier_raw) if pd.notna(row.chandelier_raw) else np.nan
            if np.isfinite(chand) and chand<float(row.close_raw) and chand>operative: operative=chand
    exp=fwd.iloc[:exit_day]
    return {"symbol":e["symbol"],"t0_date":str(t0.date()),"year":int(t0.year),"variant":variant,
            "gross_return":exit_price/entry-1,"holding_days":exit_day,"exit_reason":reason,
            "mfe":float(exp.high_raw.max()/entry-1),"mae":float(exp.low_raw.min()/entry-1)}

def summary(x):
    out={"n":len(x),"unique_symbols":int(x.symbol.nunique()),"median_hold":float(x.holding_days.median()),
         "median_mfe":float(x.mfe.median()),"median_mae":float(x.mae.median()),
         "exit_reasons":{str(k):int(v) for k,v in x.exit_reason.value_counts().items()}}
    for bps in COSTS:
        r=x.gross_return-2*bps/10000
        out[f"cost_{bps}bps_side"]={"median":float(r.median()),"mean":float(r.mean()),"positive_rate":float((r>0).mean())}
    return out

def main():
    dec,_,meta=val.build_validation_corpus()
    # Build structural events directly so acceptance remains exactly EDGE-CAND-001.
    all_events=build_edge_events(dec)
    elig=dec.loc[dec.research_eligible.astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events=all_events.merge(elig,on=["symbol","t0_date"],how="inner")
    accepted=events.loc[events.t1_accepted.astype(bool)].copy()
    groups={s:val.add_chandelier(g) for s,g in dec.groupby("symbol",sort=False)}
    rows=[]
    for _,e in accepted.iterrows():
        per=[eval_t2(groups[e.symbol],e,v) for v in ("CURRENT-ACCEPTED","EDGE+EXIT003")]
        if all(z is not None for z in per): rows.extend(per)
    df=pd.DataFrame(rows); counts=df.groupby("variant").size().to_dict()
    if not counts or len(set(counts.values()))!=1: raise RuntimeError(f"nonpaired {counts}")
    variants={v:summary(x) for v,x in df.groupby("variant")}
    cand=df[df.variant=="EDGE+EXIT003"].copy(); cand["net10"]=cand.gross_return-.002
    yearly=[]
    for y,g in cand.groupby("year"):
        yearly.append({"year":int(y),"n":len(g),"median_net10":float(g.net10.median()),"mean_net10":float(g.net10.mean()),"positive_rate_net10":float((g.net10>0).mean())})
    recent=cand[cand.year>=2022]
    cnt=Counter(cand.symbol.astype(str)); top=max(cnt.values())/len(cand) if len(cand) else None
    out={"status":"ECONOMIC_CONVERSION_FOLLOWUP_NOT_OOS","contract":"docs/EDGE_ECON_001_CONTRACT.md",
         "corpus":meta,"accepted_events_before_maturity":len(accepted),"paired_events":counts["EDGE+EXIT003"],
         "variants":variants,"yearly_candidate_net_10bps_side":yearly,
         "recent_2022_2026_net_10bps_side":None if recent.empty else {"n":len(recent),"median":float(recent.net10.median()),"mean":float(recent.net10.mean()),"positive_rate":float((recent.net10>0).mean())},
         "top_symbol_share":top,"governance":"Reporting only; no production promotion gate; no parameter tuning."}
    OUT.mkdir(parents=True,exist_ok=True); df.to_csv(OUT/"events.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
