"""Diagnostic attribution of the 2026-09-10 first-admission jump.

Read-only: reconstructs frozen decision components from current R2 READY history and
uses Supabase watchlist only to identify symbols whose first persisted admission was
2026-09-10. No R2/Supabase production state is written.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

import database
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer
from r2_ready import load_ready_dataset
from r2_feature_engine import build_feature_store_from_r2

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
    result = build_feature_store_from_r2(ready=ready, manifest=manifest)
    decided = compute_decision_layer(compute_hard_filter(result["features"]))
    decided["date"] = pd.to_datetime(decided["date"]).dt.normalize()

    rows = []
    for symbol in target_symbols:
        s = decided[decided["symbol"] == symbol].sort_values("date")
        t = s[s["date"] == TARGET]
        p = s[s["date"] == PRIOR]
        if t.empty:
            rows.append({"symbol": symbol, "error": "missing_target_row"})
            continue
        tr = t.iloc[-1]
        pr = p.iloc[-1] if not p.empty else None
        row = {
            "symbol": symbol,
            "first_watch_date": TARGET.date().isoformat(),
            "prior_date": PRIOR.date().isoformat(),
            "target_investability": tr.get("investability_status"),
            "target_stage": tr.get("stage"),
            "target_ema_aligned": tr.get("ema_stack_aligned"),
            "target_rs_spy": tr.get("rs_spy"),
            "target_avg_volume_50d": tr.get("avg_volume_50d"),
            "target_close_raw": tr.get("close_raw"),
        }
        for c in COMPONENTS:
            row[f"target_{c}"] = tr.get(c)
        if pr is None:
            row["prior_investability"] = None
            row["transition"] = "NO_PRIOR_ROW"
        else:
            row["prior_investability"] = pr.get("investability_status")
            row["prior_stage"] = pr.get("stage")
            row["prior_ema_aligned"] = pr.get("ema_stack_aligned")
            row["prior_rs_spy"] = pr.get("rs_spy")
            row["prior_avg_volume_50d"] = pr.get("avg_volume_50d")
            row["prior_close_raw"] = pr.get("close_raw")
            for c in COMPONENTS:
                row[f"prior_{c}"] = pr.get(c)
            row["transition"] = f"{pr.get('investability_status')}->{tr.get('investability_status')}"
            changed = [c.replace("_status", "") for c in COMPONENTS if pr.get(c) != tr.get(c)]
            row["changed_components"] = ",".join(changed) if changed else "NONE"
            recovered = [c.replace("_status", "") for c in COMPONENTS
                         if STATUS_RANK.get(str(pr.get(c)), -1) < STATUS_RANK.get(str(tr.get(c)), -1)]
            row["improved_components"] = ",".join(recovered) if recovered else "NONE"
        rows.append(row)

    detail = pd.DataFrame(rows)
    detail.to_csv(DETAIL, index=False)
    valid = detail[detail.get("error", pd.Series(index=detail.index, dtype=object)).isna()].copy()

    component_transitions = {}
    for c in COMPONENTS:
        a, b = f"prior_{c}", f"target_{c}"
        if a in valid and b in valid:
            component_transitions[c] = valid.groupby([a, b], dropna=False).size().sort_values(ascending=False).to_dict()
    # JSON cannot serialize tuple keys.
    component_transitions = {
        c: {f"{a}->{b}": int(n) for (a, b), n in valid.groupby([f'prior_{c}', f'target_{c}'], dropna=False).size().items()}
        for c in COMPONENTS if f"prior_{c}" in valid and f"target_{c}" in valid
    }

    summary = {
        "audit": "SEP10-FIRST-ADMISSION-ATTRIBUTION",
        "status": "DIAGNOSTIC_ONLY_NO_MUTATION",
        "target_date": TARGET.date().isoformat(),
        "comparison_date": PRIOR.date().isoformat(),
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "first_admission_symbols": len(target_symbols),
        "reconstructed_target_rows": int(len(valid)),
        "target_investability_counts": valid["target_investability"].value_counts(dropna=False).to_dict(),
        "prior_investability_counts": valid["prior_investability"].value_counts(dropna=False).to_dict(),
        "overall_transitions": valid["transition"].value_counts(dropna=False).to_dict(),
        "changed_component_sets": valid.get("changed_components", pd.Series(dtype=object)).value_counts(dropna=False).to_dict(),
        "improved_component_sets": valid.get("improved_components", pd.Series(dtype=object)).value_counts(dropna=False).to_dict(),
        "component_transitions": component_transitions,
        "historical_ema_basis_note": "Sep04/Sep10 reconstructed historical rows use legacy close_raw EMA path; canonical adj_close shared EMA replaces terminal row only.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    print("\nDETAIL")
    print(detail.to_string(index=False))


if __name__ == "__main__":
    main()
