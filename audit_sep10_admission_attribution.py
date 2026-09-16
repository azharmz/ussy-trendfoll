"""Diagnostic attribution of the 2026-09-10 first-admission jump.

Read-only. Reconstruct only the first-admission symbols from current R2 history;
no R2/Supabase production state is written.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

import database
import feature_engine as fe
from sector_cache import get_sector_map
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer
from r2_ready import load_ready_dataset, to_feature_contract

TARGET = pd.Timestamp("2026-09-10")
PRIOR = pd.Timestamp("2026-09-04")
SUMMARY = Path("sep10_admission_attribution_summary.json")
DETAIL = Path("sep10_admission_attribution.csv")
COMPONENTS = ["trend_status", "liquidity_status", "rs_status", "price_status"]


def main():
    client = database.get_client()
    history = database.get_watchlist_history(client)
    if history.empty:
        raise RuntimeError("watchlist history empty")
    first = history.groupby("symbol")["date"].min()
    target_symbols = sorted(first[first.dt.normalize() == TARGET].index.astype(str))

    ready, manifest = load_ready_dataset()
    raw = to_feature_contract(ready)
    raw = raw[raw["symbol"].isin(target_symbols)].copy()
    raw["date"] = pd.to_datetime(raw["date"]).astype("datetime64[ns]")
    found = sorted(raw["symbol"].dropna().unique())
    missing = sorted(set(target_symbols) - set(found))
    if missing:
        raise RuntimeError(f"first-admission symbols missing from R2 READY: {missing}")
    sector_map = get_sector_map(client, found)

    # Reconstruct historical rows with the same legacy feature formulas but only
    # for the 61 symbols under attribution. Shared canonical EMA migration affects
    # terminal rows only, so it is intentionally not applied to Sep04/Sep10.
    original_universe = fe.download_universe
    original_earnings = fe.compute_days_to_next_earnings
    fe.download_universe = lambda symbols: raw.copy()
    fe.compute_days_to_next_earnings = lambda ticker, as_of_date: None
    try:
        result = fe.build_feature_store(found, sector_map=sector_map)
    finally:
        fe.download_universe = original_universe
        fe.compute_days_to_next_earnings = original_earnings

    decided = compute_decision_layer(compute_hard_filter(result["features"]))
    decided["date"] = pd.to_datetime(decided["date"]).dt.normalize()

    rows = []
    for symbol in target_symbols:
        s = decided[decided["symbol"] == symbol].sort_values("date")
        t, p = s[s["date"] == TARGET], s[s["date"] == PRIOR]
        if t.empty:
            rows.append({"symbol": symbol, "error": "missing_target_row"})
            continue
        tr = t.iloc[-1]; pr = p.iloc[-1] if not p.empty else None
        row = {"symbol": symbol, "first_watch_date": TARGET.date().isoformat(),
               "prior_date": PRIOR.date().isoformat(), "target_investability": tr.get("investability_status"),
               "target_stage": tr.get("stage"), "target_ema_aligned": tr.get("ema_stack_aligned"),
               "target_rs_spy": tr.get("rs_spy"), "target_avg_volume_50d": tr.get("avg_volume_50d"),
               "target_close_raw": tr.get("close_raw")}
        for c in COMPONENTS: row[f"target_{c}"] = tr.get(c)
        if pr is None:
            row["prior_investability"] = None; row["transition"] = "NO_PRIOR_ROW"
        else:
            row.update({"prior_investability": pr.get("investability_status"), "prior_stage": pr.get("stage"),
                        "prior_ema_aligned": pr.get("ema_stack_aligned"), "prior_rs_spy": pr.get("rs_spy"),
                        "prior_avg_volume_50d": pr.get("avg_volume_50d"), "prior_close_raw": pr.get("close_raw")})
            for c in COMPONENTS: row[f"prior_{c}"] = pr.get(c)
            row["transition"] = f"{pr.get('investability_status')}->{tr.get('investability_status')}"
            changed = [c.replace("_status", "") for c in COMPONENTS if pr.get(c) != tr.get(c)]
            improved = [c.replace("_status", "") for c in COMPONENTS if STATUS_RANK.get(str(pr.get(c)),-1) < STATUS_RANK.get(str(tr.get(c)),-1)]
            row["changed_components"] = ",".join(changed) if changed else "NONE"
            row["improved_components"] = ",".join(improved) if improved else "NONE"
        rows.append(row)

    detail = pd.DataFrame(rows); detail.to_csv(DETAIL, index=False)
    valid = detail[detail.get("error", pd.Series(index=detail.index,dtype=object)).isna()].copy()
    transitions = {c:{f"{a}->{b}":int(n) for (a,b),n in valid.groupby([f"prior_{c}",f"target_{c}"],dropna=False).size().items()}
                   for c in COMPONENTS if f"prior_{c}" in valid}
    summary = {"audit":"SEP10-FIRST-ADMISSION-ATTRIBUTION","status":"DIAGNOSTIC_ONLY_NO_MUTATION",
               "target_date":TARGET.date().isoformat(),"comparison_date":PRIOR.date().isoformat(),
               "ready_snapshot_date":manifest.get("snapshot_date"),"first_admission_symbols":len(target_symbols),
               "reconstructed_target_rows":int(len(valid)),
               "target_investability_counts":valid["target_investability"].value_counts(dropna=False).to_dict(),
               "prior_investability_counts":valid["prior_investability"].value_counts(dropna=False).to_dict(),
               "overall_transitions":valid["transition"].value_counts(dropna=False).to_dict(),
               "changed_component_sets":valid.get("changed_components",pd.Series(dtype=object)).value_counts(dropna=False).to_dict(),
               "improved_component_sets":valid.get("improved_components",pd.Series(dtype=object)).value_counts(dropna=False).to_dict(),
               "component_transitions":transitions,
               "historical_ema_basis_note":"Sep04/Sep10 reconstruction uses legacy close_raw EMA path; canonical adj_close shared EMA replaces terminal row only."}
    SUMMARY.write_text(json.dumps(summary,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,default=str)); print("\nDETAIL"); print(detail.to_string(index=False))

if __name__ == "__main__": main()
