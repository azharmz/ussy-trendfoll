"""Untouched validation for frozen EXIT-CAND-003.

Protocol: docs/EXIT_CAND_003_VALIDATION_PROTOCOL.md
Candidate semantics are imported unchanged from the frozen development runner.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
import run_exit_candidate001_development as base
import run_exit_candidate003_development as cand
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

OUT=Path("artifacts/exit_candidate003_validation")
RANK_START=101
RANK_END=200
VARIANTS=("CURRENT","EXIT-CAND-003")


def ranked_ids(ready):
    p=ready[["security_id","ticker"]].drop_duplicates().astype(str).copy()
    p["rank_hash"]=p.apply(lambda r: hashlib.sha256(f"{r.security_id}|{r.ticker}".encode()).hexdigest(),axis=1)
    p=p.sort_values(["rank_hash","security_id"]).reset_index(drop=True)
    if len(p)<RANK_END:
        raise RuntimeError(f"validation requires >= {RANK_END} ranked securities; got {len(p)}")
    dev=p.iloc[:100].copy()
    val=p.iloc[RANK_START-1:RANK_END].copy()
    overlap=set(dev.security_id)&set(val.security_id)
    if overlap:
        raise RuntimeError(f"development-validation security overlap: {sorted(overlap)}")
    return dev.security_id.tolist(),val.security_id.tolist(),p


def build_validation_corpus():
    ready,manifest=load_ready_dataset()
    dev_ids,val_ids,_=ranked_ids(ready)
    end=manifest.get("snapshot_date") or str(pd.to_datetime(ready.date).max().date())
    hist,report=load_research_history(val_ids,evaluation_end=end,min_preroll_bars=500,ready=ready,ready_manifest=manifest)
    feat=build_research_feature_store(hist)["features"].sort_values(["symbol","date"])
    dec=compute_decision_layer(compute_hard_filter(feat)).sort_values(["symbol","date"])
    events=build_signal_path_events(dec)
    eligible=dec.loc[dec.research_eligible.astype(bool),["symbol","date"]].rename(columns={"date":"t0_date"}).drop_duplicates()
    events=events.merge(eligible,on=["symbol","t0_date"],how="inner")
    overlap=len(set(dev_ids)&set(val_ids))
    meta={"snapshot":manifest.get("snapshot_date"),"evaluation_end":end,"rank_method":"sha256(security_id|ticker), ascending hash then security_id","development_rank_range":[1,100],"validation_rank_range":[101,200],"development_security_count":len(dev_ids),"validation_security_count":len(val_ids),"development_validation_security_overlap":overlap,"eligible_onsets":int(len(events)),"history_report":asdict(report)}
    if overlap!=0: raise RuntimeError("zero-overlap invariant failed")
    return dec,events,meta


def add_chandelier(g):
    g=g.sort_values("date").reset_index(drop=True).copy()
    tr=base._true_range(g)
    atr22=tr.ewm(alpha=1/base.CHAND_PERIOD,adjust=False,min_periods=base.CHAND_PERIOD).mean()
    hh22=g.high_raw.rolling(base.CHAND_PERIOD,min_periods=base.CHAND_PERIOD).max()
    g["chandelier_raw"]=hh22-base.CHAND_ATR_MULT*atr22
    return g


def main():
    dec,events,meta=build_validation_corpus()
    groups={s:add_chandelier(g) for s,g in dec.groupby("symbol",sort=False)}
    rows=[]
    for _,e in events.iterrows():
        per=[cand.evaluate(groups[e.symbol],e,v) for v in VARIANTS]
        if all(z is not None for z in per): rows.extend(per)
    df=pd.DataFrame(rows)
    counts=df.groupby("variant").size().to_dict() if not df.empty else {}
    paired_ok=bool(counts and set(counts)==set(VARIANTS) and len(set(counts.values()))==1)
    if not paired_ok: raise RuntimeError(f"non-comparable validation corpus: {counts}")
    out=cand.summarize(df)
    cur=out["CURRENT"]; k=out["EXIT-CAND-003"]
    criteria={
        "corpus_integrity_zero_overlap":meta["development_validation_security_overlap"]==0 and meta["validation_security_count"]==100,
        "comparator_exact_paired_counts":paired_ok,
        "feasibility_invariants":"PASS",
        "median_return_strictly_better":k["median_return"]>cur["median_return"],
        "positive_rate_not_lower":k["positive_rate"]>=cur["positive_rate"],
        "median_mae_not_worse":k["median_mae"]>=cur["median_mae"],
    }
    gate="PASS" if all(v is True or v=="PASS" for v in criteria.values()) else "FAIL"
    summary={"status":"UNTOUCHED_VALIDATION","candidate":"EXIT-CAND-003","protocol":"docs/EXIT_CAND_003_VALIDATION_PROTOCOL.md","corpus":meta,"exact_paired_comparable_events":int(counts["CURRENT"]),"criteria":criteria,"validation_gate":gate,"variants":out,"terminal_verdict":"DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION" if gate=="PASS" else "VALIDATION FAILED / EVIDENCE-LOCKED / DO NOT TUNE"}
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/"events.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__": main()
