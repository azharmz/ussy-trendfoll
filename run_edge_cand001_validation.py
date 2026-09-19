"""Untouched validation for frozen EDGE-CAND-001."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from edge_decomposition import build_edge_events

DEV_N=100
OOS_N=100

def ranked(ready):
    p=ready[["security_id","ticker"]].drop_duplicates().copy()
    p["security_id"]=p["security_id"].astype(str); p["ticker"]=p["ticker"].astype(str)
    p["rank_key"]=p.apply(lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(),axis=1)
    return p.sort_values(["rank_key","security_id"]).reset_index(drop=True)

def stats(frame,col):
    x=frame[col].dropna()
    return {"n":int(len(x)),"median":None if x.empty else float(x.median()),
            "mean":None if x.empty else float(x.mean()),
            "positive_rate":None if x.empty else float((x>0).mean())}

def main():
    ready,manifest=load_ready_dataset(); ranks=ranked(ready)
    dev=set(ranks.iloc[:DEV_N]["security_id"])
    hold=ranks.iloc[DEV_N:DEV_N+OOS_N].copy()
    hold_ids=hold["security_id"].tolist()
    if dev & set(hold_ids): raise ValueError("development/holdout overlap")
    if len(hold_ids)!=OOS_N: raise ValueError("insufficient untouched securities")
    end=manifest.get("snapshot_date") or str(pd.to_datetime(ready["date"]).max().date())
    hist,report=load_research_history(hold_ids,evaluation_end=end,min_preroll_bars=500,ready=ready,ready_manifest=manifest)
    features=build_research_feature_store(hist)["features"].sort_values(["symbol","date"])
    decided=compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol","date"])
    all_events=build_edge_events(decided)
    eligible=decided.loc[decided["research_eligible"].astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events=all_events.merge(eligible.assign(_eligible=True),on=["symbol","t0_date"],how="inner").drop(columns="_eligible")
    cand=events.loc[events["t1_accepted"].astype(bool)].copy()
    cand["year"]=pd.to_datetime(cand["t0_date"]).dt.year
    yearly=[]
    for year,g in cand.groupby("year"):
        s=stats(g,"ret_t2open_t10close"); yearly.append({"year":int(year),**s})
    mature=cand.loc[cand["ret_t2open_t10close"].notna()]
    counts=Counter(mature["symbol"].astype(str))
    top_share=(max(counts.values())/len(mature)) if len(mature) else None
    eligible_years=[x for x in yearly if x["n"]>=20]
    nonneg_year_share=(sum(x["median"]>=0 for x in eligible_years)/len(eligible_years)) if eligible_years else None
    baseline_mae=events["mae_t1_h10"].dropna(); cand_mae=cand["mae_t2_h10"].dropna()
    gates={
      "mature_t10_ge_200":len(mature)>=200,
      "unique_symbols_ge_25":mature["symbol"].nunique()>=25,
      "median_t10_positive":stats(cand,"ret_t2open_t10close")["median"] is not None and stats(cand,"ret_t2open_t10close")["median"]>0,
      "positive_rate_gt_50pct":stats(cand,"ret_t2open_t10close")["positive_rate"] is not None and stats(cand,"ret_t2open_t10close")["positive_rate"]>0.5,
      "mae10_less_adverse_than_baseline":not baseline_mae.empty and not cand_mae.empty and float(cand_mae.median())>float(baseline_mae.median()),
      "nonnegative_year_share_ge_60pct":nonneg_year_share is not None and nonneg_year_share>=0.60,
      "top_symbol_share_le_10pct":top_share is not None and top_share<=0.10,
    }
    out={"candidate":"EDGE-CAND-001","status":"UNTOUCHED_VALIDATION","ready_snapshot_date":manifest.get("snapshot_date"),
         "holdout_rank_range":"101-200","holdout_requested":len(hold_ids),"research_contract":asdict(report),
         "full_history_onsets":len(all_events),"eligible_onsets":len(events),"candidate_events":len(cand),
         "participation_rate":None if len(events)==0 else len(cand)/len(events),
         "baseline_t1_t5":stats(events,"ret_t1open_t5close"),"baseline_t1_t10":stats(events,"ret_t1open_t10close"),
         "candidate_t2_t5":stats(cand,"ret_t2open_t5close"),"candidate_t2_t10":stats(cand,"ret_t2open_t10close"),
         "baseline_mae10_median":None if baseline_mae.empty else float(baseline_mae.median()),
         "candidate_mae10_median":None if cand_mae.empty else float(cand_mae.median()),
         "candidate_mfe10_median":None if cand["mfe_t2_h10"].dropna().empty else float(cand["mfe_t2_h10"].dropna().median()),
         "candidate_unique_symbols":int(mature["symbol"].nunique()),"top_symbol_share":top_share,
         "yearly":yearly,"eligible_years_ge20":len(eligible_years),"nonnegative_year_share":nonneg_year_share,
         "gates":gates,"all_gates_pass":all(gates.values()),
         "governance":"Frozen untouched validation only; no production change is authorized by this runner."}
    Path("edge_cand001_validation.json").write_text(json.dumps(out,indent=2,default=str),encoding="utf-8")
    events.to_csv("edge_cand001_holdout_events.csv",index=False)
    print(json.dumps(out,indent=2,default=str))

if __name__=="__main__": main()
