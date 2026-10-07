"""Audit all production stop-loss exits against canonical READY OHLC; read-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r2_ready import load_ready_dataset

# symbol, exit_date, stop_price, realistic_entry_price, production_exit_price
TARGETS = [
    ("CRSR", "2026-08-17", 12.557627066116893, 14.859999656677246, 12.557627066116893),
    ("FSLY", "2026-08-19", 23.714605639462896, 27.649999618530273, 23.714605639462896),
    ("NUE", "2026-08-19", 257.554103465163, 274.5199890136719, 257.554103465163),
    ("WSM", "2026-08-20", 233.63981948491954, 247.69000244140625, 233.63981948491954),
    ("ANF", "2026-08-26", 132.35252353126424, 144.6999969482422, 132.35252353126424),
    ("LLY", "2026-08-26", 1195.6366675506667, 1274.1300048828125, 1195.6366675506667),
    ("ACAD", "2026-08-31", 28.752092852848735, 30.65999984741211, 28.752092852848737),
    ("BHP", "2026-09-04", 92.17488778840444, 97.30999755859375, 92.17488778840443),
    ("FTNT", "2026-09-04", 159.07229757502069, 172.5800018310547, 159.07229757502068),
    ("SLB", "2026-09-04", 56.39301263726229, 60.0, 56.39301263726229),
    ("BDX", "2026-09-10", 182.56816832993704, 191.72999572753906, 182.56816832993704),
    ("CRWD", "2026-09-10", 205.2781810723855, 228.4949951171875, 205.2781810723855),
    ("NVS", "2026-09-10", 153.82292699338223, 160.8000030517578, 153.82292699338223),
    ("NEO", "2026-09-23", 18.302146253745367, 19.920000076293945, 18.302146253745367),
    ("FIVN", "2026-09-28", 34.974395178860945, 38.9900016784668, 34.974395178860945),
    ("ATRC", "2026-10-02", 54.5063149150305, 58.5099983215332, 54.5063149150305),
    ("BLFS", "2026-10-02", 37.12774811921547, 39.16999816894531, 37.12774811921547),
    ("RGEN", "2026-10-02", 181.95264922991925, 196.0, 181.95264922991925),
]


def main() -> None:
    frame, manifest = load_ready_dataset()
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    rows = []
    for symbol, date_text, stop, entry, prod_exit in TARGETS:
        date = pd.Timestamp(date_text)
        matches = frame.loc[(frame["ticker"] == symbol) & (frame["date"] == date)]
        row = {
            "symbol": symbol, "exit_date": date_text, "match_count": len(matches),
            "stop_price": stop, "realistic_entry_price": entry,
            "production_exit_price": prod_exit,
        }
        if len(matches) != 1:
            row["status"] = "NOT_IN_READY" if len(matches) == 0 else "AMBIGUOUS_DUPLICATE"
        else:
            hit = matches.iloc[0]
            open_price, low_price = float(hit["open"]), float(hit["low"])
            row.update({
                "status": "FOUND", "security_id": str(hit["security_id"]),
                "open": open_price, "high": float(hit["high"]), "low": low_price,
                "close": float(hit["close"]), "adj_close": float(hit["adj_close"]),
                "volume": float(hit["volume"]),
                "classification": "GAP_THROUGH" if open_price <= stop else ("INTRADAY_TOUCH" if low_price <= stop else "STOP_NOT_TOUCHED"),
                "open_fill_assumption": min(open_price, stop) if low_price <= stop else None,
                "production_return_pct": (prod_exit / entry - 1) * 100,
                "open_fill_return_pct": (min(open_price, stop) / entry - 1) * 100 if low_price <= stop else None,
                "return_delta_pp": ((min(open_price, stop) - prod_exit) / entry) * 100 if low_price <= stop else None,
            })
        rows.append(row)

    result = pd.DataFrame(rows)
    out = Path("artifacts/stop_loss_execution_audit.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    found = result[result["status"] == "FOUND"]
    gap = found[found["classification"] == "GAP_THROUGH"]
    touch = found[found["classification"] == "INTRADAY_TOUCH"]
    deltas = found["return_delta_pp"].dropna()
    summary = {
        "ready_schema_version": manifest.get("schema_version"),
        "ready_as_of_date": manifest.get("as_of_date"),
        "ready_parquet_key": manifest.get("parquet_key"),
        "ready_rows": len(frame), "targets": len(result),
        "found": int((result["status"] == "FOUND").sum()),
        "not_in_ready": int((result["status"] == "NOT_IN_READY").sum()),
        "ambiguous": int((result["status"] == "AMBIGUOUS_DUPLICATE").sum()),
        "gap_through": len(gap), "intraday_touch": len(touch),
        "stop_not_touched": int((found["classification"] == "STOP_NOT_TOUCHED").sum()),
        "gap_mean_return_delta_pp": float(deltas[found.loc[deltas.index, "classification"] == "GAP_THROUGH"].mean()) if len(gap) else None,
        "all_touched_mean_return_delta_pp": float(deltas.mean()) if len(deltas) else None,
        "all_touched_sum_trade_deltas_pp_unweighted": float(deltas.sum()) if len(deltas) else None,
        "csv": str(out),
    }
    Path("artifacts/stop_loss_execution_audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(result.to_string(index=False))
    if summary["not_in_ready"] or summary["ambiguous"]:
        raise SystemExit("Some target OHLC rows are missing or ambiguous; review required.")


if __name__ == "__main__":
    main()
