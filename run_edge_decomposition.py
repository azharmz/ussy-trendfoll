"""Run governed TrendFoll edge decomposition on research history."""
from __future__ import annotations
import hashlib, json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from edge_decomposition import build_edge_events, summarize

SAMPLE_SIZE=100

def sample_ids(ready):
    p=ready[["security_id","ticker"]].drop_duplicates().copy()
    p["security_id"]=p["security_id"].astype(str); p["ticker"]=p["ticker"].astype(str)
    p["rank"]=p.apply(lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(),axis=1)
    return p.sort_values(["rank","security_id"]).head(SAMPLE_SIZE)["security_id"].tolist()

def main():
    ready,manifest=load_ready_dataset(); ids=sample_ids(ready)
    end=manifest.get("snapshot_date") or str(pd.to_datetime(ready["date"]).max().date())
    hist,report=load_research_history(ids,evaluation_end=end,min_preroll_bars=500,ready=ready,ready_manifest=manifest)
    features=build_research_feature_store(hist)["features"].sort_values(["symbol","date"]).copy()
    decided=compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol","date"]).copy()
    all_events=build_edge_events(decided)
    eligible=decided.loc[decided["research_eligible"].astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events=all_events.merge(eligible.assign(_eligible=True),on=["symbol","t0_date"],how="inner").drop(columns="_eligible")
    s=summarize(events)
    s.update({"contract":"docs/EDGE_DECOMPOSITION_CONTRACT.md","ready_snapshot_date":manifest.get("snapshot_date"),
              "sample_size":len(ids),"research_contract":asdict(report),"all_full_history_onsets":int(len(all_events)),
              "eligible_onsets":int(len(events)),"survivorship":"current READY universe; not PIT historical membership"})
    events.to_csv("edge_decomposition_events.csv",index=False)
    Path("edge_decomposition_summary.json").write_text(json.dumps(s,indent=2,default=str),encoding="utf-8")
    print(json.dumps(s,indent=2,default=str))

if __name__=="__main__": main()
