"""Governed development evaluation for frozen EXIT-CAND-002.
No parameter search; fail closed on execution-feasibility violations.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import run_exit_candidate001_development as base

OUT=Path("artifacts/exit_candidate002_development")
MAX_HOLD=45
VARIANTS=("CURRENT","EXIT-CAND-002")
BASELINE={"n":1524,"median_return":-0.034647603839578656,"positive_rate":0.3300524934383202,"median_mae":-0.047341183038064116}
TOL=1e-12

def evaluate(g,event,variant):
    g=g.sort_values("date").reset_index(drop=True); t0=pd.Timestamp(event["t0_date"])
    ix=g.index[g.date==t0]
    if len(ix)!=1 or ix[0]+MAX_HOLD>=len(g): return None
    i0=int(ix[0]); entry_i=i0+1; entry=float(g.iloc[entry_i].open_raw)
    atr0=float(g.iloc[i0].atr14) if pd.notna(g.iloc[i0].atr14) else np.nan
    if not np.isfinite(entry) or not np.isfinite(atr0) or atr0<=0:return None
    initial_stop=entry-2.0*atr0; operative_stop=initial_stop
    fwd=g.iloc[entry_i:entry_i+MAX_HOLD].reset_index(drop=True)
    reason="max_holding" if variant=="CURRENT" else "observation_boundary"
    exit_day=MAX_HOLD; exit_price=float(fwd.iloc[-1].close_raw)
    stop_path=[]
    for j,row in fwd.iterrows():
        day=j+1; stop_today=initial_stop if variant=="CURRENT" else operative_stop
        if variant!="CURRENT":
            if stop_path and stop_today < stop_path[-1]-TOL: raise RuntimeError("operative stop decreased")
            stop_path.append(stop_today)
        lo=float(row.low_raw); hi=float(row.high_raw)
        if lo<=stop_today:
            if stop_today>hi+TOL or stop_today<lo-TOL: raise RuntimeError(f"infeasible stop fill {event['symbol']} {t0.date()} d{day}: low={lo} stop={stop_today} high={hi}")
            reason="stop_loss" if variant=="CURRENT" else "risk_stop"; exit_day=day; exit_price=stop_today; break
        if day>=MAX_HOLD: break
        if pd.notna(row.ema20) and float(row.close_raw)<float(row.ema20):
            reason="trend_exit"; exit_day=day; exit_price=float(row.close_raw); break
        if variant!="CURRENT":
            chand=float(row.chandelier_raw) if pd.notna(row.chandelier_raw) else np.nan
            close=float(row.close_raw)
            if np.isfinite(chand) and chand < close and chand > operative_stop:
                operative_stop=chand
    exp=fwd.iloc[:exit_day]; max_close=max(entry,float(exp.close_raw.max()))
    return {"symbol":event["symbol"],"t0_date":str(t0.date()),"variant":variant,"entry_price":entry,"exit_price":exit_price,
      "realized_return":exit_price/entry-1,"holding_days":exit_day,"exit_reason":reason,
      "mfe_to_exit":float(exp.high_raw.max()/entry-1),"mae_to_exit":float(exp.low_raw.min()/entry-1),"giveback":exit_price/max_close-1}

def summarize(df):
    out={}
    for v,x in df.groupby("variant"):
        r=x.realized_return
        out[v]={"n":int(len(x)),"median_return":float(r.median()),"positive_rate":float((r>0).mean()),
          "q25_return":float(r.quantile(.25)),"q75_return":float(r.quantile(.75)),"median_holding":float(x.holding_days.median()),
          "median_mfe":float(x.mfe_to_exit.median()),"median_mae":float(x.mae_to_exit.median()),"median_giveback":float(x.giveback.median()),
          "exit_reasons":{str(k):int(n) for k,n in x.exit_reason.value_counts().items()},"stop_touch_timing":base.stop_timing(x,v)}
    cur=df[df.variant=="CURRENT"].set_index(["symbol","t0_date"]).realized_return
    cand=df[df.variant=="EXIT-CAND-002"].set_index(["symbol","t0_date"]).realized_return; d=cand-cur
    out["EXIT-CAND-002"].update({"median_return_difference_vs_current":out["EXIT-CAND-002"]["median_return"]-out["CURRENT"]["median_return"],
      "paired_event_delta_median_vs_current":float(d.median()),"improved_fraction":float((d>1e-12).mean()),
      "worsened_fraction":float((d<-1e-12).mean()),"unchanged_fraction":float((d.abs()<=1e-12).mean())})
    return out

def main():
    dec,events,meta=base.build_corpus()
    # Candidate needs same-bar Chandelier value only AFTER that bar survives; no shift here.
    groups={}
    for s,g in dec.groupby("symbol",sort=False):
        g=g.sort_values("date").reset_index(drop=True).copy(); tr=base._true_range(g)
        atr22=tr.ewm(alpha=1/base.CHAND_PERIOD,adjust=False,min_periods=base.CHAND_PERIOD).mean()
        hh22=g.high_raw.rolling(base.CHAND_PERIOD,min_periods=base.CHAND_PERIOD).max()
        g["chandelier_raw"]=hh22-base.CHAND_ATR_MULT*atr22; groups[s]=g
    rows=[]
    for _,e in events.iterrows():
        per=[evaluate(groups[e.symbol],e,v) for v in VARIANTS]
        if all(z is not None for z in per): rows.extend(per)
    df=pd.DataFrame(rows); counts=df.groupby("variant").size().to_dict()
    if not counts or set(counts)!=set(VARIANTS) or len(set(counts.values()))!=1: raise RuntimeError(f"non-comparable corpus: {counts}")
    out=summarize(df); c=out["CURRENT"]; k=out["EXIT-CAND-002"]
    baseline_ok=(c["n"]==BASELINE["n"] and abs(c["median_return"]-BASELINE["median_return"])<=TOL and abs(c["positive_rate"]-BASELINE["positive_rate"])<=TOL and abs(c["median_mae"]-BASELINE["median_mae"])<=TOL)
    criteria={"current_baseline_exact":baseline_ok,"median_return_strictly_better":k["median_return"]>c["median_return"],
      "positive_rate_not_lower":k["positive_rate"]>=c["positive_rate"],"median_mae_not_worse":k["median_mae"]>=c["median_mae"],"feasibility_invariants":"PASS"}
    summary={"status":"DEVELOPMENT_ONLY_NOT_VALIDATION","candidate":"EXIT-CAND-002","representation":{"initial_stop":"entry - 2*ATR14(T0)","chandelier":"HH22 - 3*WilderATR22","activation":"after surviving day t, arm for t+1 only when finite and chandelier_t < close_t and > operative_stop","ema20":"retained","observation_boundary":45},"corpus":meta,"criteria":criteria,"development_gate":"PASS" if all(v is True or v=="PASS" for v in criteria.values()) else "FAIL","variants":out}
    if not baseline_ok: raise RuntimeError("CURRENT failed EXIT-ISO-001 baseline consistency")
    OUT.mkdir(parents=True,exist_ok=True); df.to_csv(OUT/"events.csv",index=False); (OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
