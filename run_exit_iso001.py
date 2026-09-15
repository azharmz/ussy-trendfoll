"""EXIT-ISO-001: isolate current exit-stack components without parameter tuning."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

SAMPLE_SIZE=100; ATR_MULT=2.0; MAX_HOLD=45
VARIANTS={
 "CURRENT":(True,True),
 "NO_STOP":(False,True),
 "NO_EMA20":(True,False),
 "DAY45_ONLY":(False,False),
}

def sample_ids(ready):
 p=ready[["security_id","ticker"]].drop_duplicates().astype(str)
 p["rank"]=p.apply(lambda r: hashlib.sha256(f"{r.security_id}|{r.ticker}".encode()).hexdigest(),axis=1)
 return p.sort_values(["rank","security_id"]).head(SAMPLE_SIZE)["security_id"].tolist()

def med(s):
 s=pd.Series(s).dropna(); return None if s.empty else float(s.median())

def q(s,p):
 s=pd.Series(s).dropna(); return None if s.empty else float(s.quantile(p))

def evaluate(g,event,use_stop,use_ema):
 g=g.sort_values("date").reset_index(drop=True); t0=pd.Timestamp(event["t0_date"])
 ix=g.index[g["date"]==t0]
 if len(ix)!=1 or ix[0]+MAX_HOLD>=len(g): return None
 i0=int(ix[0]); entry_i=i0+1; entry=g.iloc[entry_i]; entry_px=float(entry["open_raw"])
 atr=float(g.iloc[i0]["atr14"]) if pd.notna(g.iloc[i0]["atr14"]) else np.nan
 if not np.isfinite(entry_px) or not np.isfinite(atr) or atr<=0:return None
 stop=entry_px-ATR_MULT*atr; fwd=g.iloc[entry_i:entry_i+MAX_HOLD].reset_index(drop=True)
 reason="max_holding"; exit_day=MAX_HOLD; exit_px=float(fwd.iloc[-1]["close_raw"])
 for j,r in fwd.iterrows():
  day=j+1
  if use_stop and float(r["low_raw"])<=stop:
   reason="stop_loss"; exit_day=day; exit_px=stop; break
  if day>=MAX_HOLD: break
  if use_ema and pd.notna(r.get("ema20")) and float(r["close_raw"])<float(r["ema20"]):
   reason="trend_exit"; exit_day=day; exit_px=float(r["close_raw"]); break
 exp=fwd.iloc[:exit_day]
 max_close=max(entry_px,float(exp["close_raw"].max()))
 return {"symbol":event["symbol"],"t0_date":str(t0.date()),"entry_price":entry_px,
  "exit_reason":reason,"exit_day":exit_day,"exit_price":exit_px,"realized_return":exit_px/entry_px-1,
  "mfe_to_exit":float(exp["high_raw"].max()/entry_px-1),"mae_to_exit":float(exp["low_raw"].min()/entry_px-1),
  "giveback":exit_px/max_close-1}

def summary(df):
 r=df.realized_return
 return {"n":int(len(df)),"median_return":med(r),"positive_rate":float((r>0).mean()),"q25":q(r,.25),"q75":q(r,.75),
  "median_holding":med(df.exit_day),"median_mfe":med(df.mfe_to_exit),"median_mae":med(df.mae_to_exit),"median_giveback":med(df.giveback),
  "exit_reasons":{str(k):int(v) for k,v in df.exit_reason.value_counts().items()}}

def main():
 ready,manifest=load_ready_dataset(); ids=sample_ids(ready)
 end=manifest.get("snapshot_date") or str(pd.to_datetime(ready.date).max().date())
 hist,_=load_research_history(ids,evaluation_end=end,min_preroll_bars=500,ready=ready,ready_manifest=manifest)
 feat=build_research_feature_store(hist)["features"].sort_values(["symbol","date"])
 dec=compute_decision_layer(compute_hard_filter(feat)).sort_values(["symbol","date"])
 events=build_signal_path_events(dec)
 eligible=dec.loc[dec.research_eligible.astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
 events=events.merge(eligible,on=["symbol","t0_date"],how="inner")
 groups={s:g for s,g in dec.groupby("symbol",sort=False)}
 rows=[]
 for _,e in events.iterrows():
  per={}
  for name,(us,ue) in VARIANTS.items(): per[name]=evaluate(groups[e.symbol],e,us,ue)
  if all(v is not None for v in per.values()):
   for name,v in per.items(): v["variant"]=name; rows.append(v)
 out=pd.DataFrame(rows); current=out[out.variant=="CURRENT"][["symbol","t0_date","realized_return"]].rename(columns={"realized_return":"current_return"})
 out=out.merge(current,on=["symbol","t0_date"],how="left"); out["delta_vs_current"]=out.realized_return-out.current_return
 summaries={}
 for name in VARIANTS:
  d=out[out.variant==name].copy(); s=summary(d); delta=d.delta_vs_current
  s["delta_vs_current_median"]=med(delta); s["improved_fraction"]=float((delta>1e-12).mean()); s["worsened_fraction"]=float((delta<-1e-12).mean()); s["unchanged_fraction"]=float((delta.abs()<=1e-12).mean()); summaries[name]=s
 payload={"diagnostic":"EXIT-ISO-001","status":"COMPONENT_ATTRIBUTION_ONLY_NO_PRODUCTION_CHANGE","snapshot":manifest.get("snapshot_date"),
  "sample_size":len(ids),"eligible_onsets":int(len(events)),"exact_45bar_comparable_events":int(out[out.variant=="CURRENT"].shape[0]),
  "variants":summaries,"governance":{"atr_multiplier":2.0,"ema_period":20,"max_hold":45,"optimization":"none","production_change":"none"}}
 out.to_csv("exit_iso001_events.csv",index=False); Path("exit_iso001_summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
