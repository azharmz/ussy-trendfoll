"""Governed development evaluation for frozen EXIT-CAND-001 / 001B.

Representation is frozen in docs/EXIT_CANDIDATE_REPRESENTATION_001.md.
No parameter search is performed here.
"""
from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import run_exit_iso001 as iso
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

OUT=Path("artifacts/exit_candidate001_development")
MAX_HOLD=45; CHAND_PERIOD=22; CHAND_ATR_MULT=3.0
VARIANTS=("CURRENT","EXIT-CAND-001","EXIT-CAND-001B")

def build_corpus():
    """Exact EXIT-ISO-001 governed corpus construction; engineering extraction only."""
    ready,manifest=load_ready_dataset(); ids=iso.sample_ids(ready)
    end=manifest.get("snapshot_date") or str(pd.to_datetime(ready.date).max().date())
    hist,report=load_research_history(ids,evaluation_end=end,min_preroll_bars=500,ready=ready,ready_manifest=manifest)
    feat=build_research_feature_store(hist)["features"].sort_values(["symbol","date"])
    dec=compute_decision_layer(compute_hard_filter(feat)).sort_values(["symbol","date"])
    events=build_signal_path_events(dec)
    eligible=dec.loc[dec.research_eligible.astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events=events.merge(eligible,on=["symbol","t0_date"],how="inner")
    meta={"snapshot":manifest.get("snapshot_date"),"sample_size":len(ids),"eligible_onsets":int(len(events)),"history_report":asdict(report)}
    return dec,events,meta

def _true_range(g):
    prev=g.close_raw.shift(1)
    return pd.concat([g.high_raw-g.low_raw,(g.high_raw-prev).abs(),(g.low_raw-prev).abs()],axis=1).max(axis=1)

def add_chandelier(g):
    g=g.copy(); tr=_true_range(g)
    atr22=tr.ewm(alpha=1/CHAND_PERIOD,adjust=False,min_periods=CHAND_PERIOD).mean()
    hh22=g.high_raw.rolling(CHAND_PERIOD,min_periods=CHAND_PERIOD).max()
    g["chandelier_prior"]=(hh22-CHAND_ATR_MULT*atr22).shift(1)
    return g

def evaluate(g,event,variant):
    g=g.sort_values("date").reset_index(drop=True); t0=pd.Timestamp(event["t0_date"])
    ix=g.index[g.date==t0]
    if len(ix)!=1 or ix[0]+MAX_HOLD>=len(g): return None
    i0=int(ix[0]); entry_i=i0+1; entry=float(g.iloc[entry_i].open_raw)
    atr0=float(g.iloc[i0].atr14) if pd.notna(g.iloc[i0].atr14) else np.nan
    if not np.isfinite(entry) or not np.isfinite(atr0) or atr0<=0:return None
    initial_stop=entry-2.0*atr0; operative_stop=initial_stop
    fwd=g.iloc[entry_i:entry_i+MAX_HOLD].reset_index(drop=True)
    reason="max_holding"; exit_day=MAX_HOLD; exit_price=float(fwd.iloc[-1].close_raw)
    for j,row in fwd.iterrows():
        day=j+1
        if variant=="CURRENT": stop_today=initial_stop
        else:
            prior=float(row.chandelier_prior) if pd.notna(row.chandelier_prior) else np.nan
            if np.isfinite(prior): operative_stop=max(operative_stop,prior)
            stop_today=operative_stop
        if float(row.low_raw)<=stop_today:
            reason="stop_loss" if variant=="CURRENT" else "risk_stop"; exit_day=day; exit_price=stop_today; break
        if day>=MAX_HOLD: break
        if variant in ("CURRENT","EXIT-CAND-001") and pd.notna(row.ema20) and float(row.close_raw)<float(row.ema20):
            reason="trend_exit"; exit_day=day; exit_price=float(row.close_raw); break
    exp=fwd.iloc[:exit_day]
    max_close=max(entry,float(exp.close_raw.max()))
    return {"symbol":event["symbol"],"t0_date":str(t0.date()),"variant":variant,"entry_price":entry,"exit_price":exit_price,
            "realized_return":exit_price/entry-1,"holding_days":exit_day,"exit_reason":reason,
            "mfe_to_exit":float(exp.high_raw.max()/entry-1),"mae_to_exit":float(exp.low_raw.min()/entry-1),"giveback":exit_price/max_close-1}

def summarize(df):
    out={}
    for variant,x in df.groupby("variant"):
        r=x.realized_return
        out[variant]={"n":int(len(x)),"median_return":float(r.median()),"positive_rate":float((r>0).mean()),
          "q25_return":float(r.quantile(.25)),"q75_return":float(r.quantile(.75)),"median_holding":float(x.holding_days.median()),
          "median_mfe":float(x.mfe_to_exit.median()),"median_mae":float(x.mae_to_exit.median()),"median_giveback":float(x.giveback.median()),
          "exit_reasons":{str(k):int(v) for k,v in x.exit_reason.value_counts().items()}}
    current=df[df.variant=="CURRENT"].set_index(["symbol","t0_date"]).realized_return
    for variant in VARIANTS[1:]:
        x=df[df.variant==variant].set_index(["symbol","t0_date"]).realized_return; d=x-current
        out[variant]["median_return_difference_vs_current"]=out[variant]["median_return"]-out["CURRENT"]["median_return"]
        out[variant]["paired_event_delta_median_vs_current"]=float(d.median())
        out[variant]["improved_fraction"]=float((d>1e-12).mean()); out[variant]["worsened_fraction"]=float((d<-1e-12).mean()); out[variant]["unchanged_fraction"]=float((d.abs()<=1e-12).mean())
    return out

def main():
    dec,events,meta=build_corpus(); groups={s:add_chandelier(g.reset_index(drop=True)) for s,g in dec.groupby("symbol",sort=False)}
    rows=[]
    for _,e in events.iterrows():
        per=[evaluate(groups[e.symbol],e,v) for v in VARIANTS]
        if all(z is not None for z in per): rows.extend(per)
    df=pd.DataFrame(rows); counts=df.groupby("variant").size().to_dict()
    if not counts or set(counts)!=set(VARIANTS) or len(set(counts.values()))!=1: raise RuntimeError(f"non-comparable candidate corpus: {counts}")
    summary={"status":"DEVELOPMENT_ONLY_NOT_VALIDATION","representation":{"chandelier_period":22,"chandelier_atr_multiplier":3.0,"lookahead_guard":"day-t stop uses Chandelier through t-1","initial_stop":"entry - 2*ATR14(T0)","max_observation_days":45},"corpus":meta,"variants":summarize(df)}
    OUT.mkdir(parents=True,exist_ok=True); df.to_csv(OUT/"events.csv",index=False); (OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
