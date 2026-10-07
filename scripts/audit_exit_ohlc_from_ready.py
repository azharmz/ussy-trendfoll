"""Read-only audit of missing TrendFoll stop-loss exit OHLC from canonical READY."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r2_ready import load_ready_dataset

TARGETS = [
    ("CRSR", "2026-08-17"),
    ("FSLY", "2026-08-19"),
    ("NUE", "2026-08-19"),
    ("WSM", "2026-08-20"),
    ("ANF", "2026-08-26"),
    ("LLY", "2026-08-26"),
    ("ACAD", "2026-08-31"),
    ("BHP", "2026-09-04"),
    ("FTNT", "2026-09-04"),
    ("SLB", "2026-09-04"),
    ("BDX", "2026-09-10"),
    ("CRWD", "2026-09-10"),
    ("NVS", "2026-09-10"),
]

def main() -> None:
    frame, manifest = load_ready_dataset()
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()

    rows = []
    for ticker, date_text in TARGETS:
        date = pd.Timestamp(date_text)
        matches = frame.loc[(frame["ticker"] == ticker) & (frame["date"] == date)]
        row = {"symbol": ticker, "exit_date": date_text, "match_count": len(matches)}
        if len(matches) == 1:
            hit = matches.iloc[0]
            row.update({
                "status": "FOUND",
                "security_id": str(hit["security_id"]),
                "open": hit["open"],
                "high": hit["high"],
                "low": hit["low"],
                "close": hit["close"],
                "adj_close": hit["adj_close"],
                "volume": hit["volume"],
            })
        elif len(matches) == 0:
            row["status"] = "NOT_IN_READY"
        else:
            row["status"] = "AMBIGUOUS_DUPLICATE"
        rows.append(row)

    result = pd.DataFrame(rows)
    out = Path("artifacts/exit_ohlc_ready_audit.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    summary = {
        "ready_schema_version": manifest.get("schema_version"),
        "ready_as_of_date": manifest.get("as_of_date"),
        "ready_parquet_key": manifest.get("parquet_key"),
        "ready_rows": len(frame),
        "targets": len(result),
        "found": int((result["status"] == "FOUND").sum()),
        "not_in_ready": int((result["status"] == "NOT_IN_READY").sum()),
        "ambiguous": int((result["status"] == "AMBIGUOUS_DUPLICATE").sum()),
        "csv": str(out),
    }
    Path("artifacts/exit_ohlc_ready_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(result.to_string(index=False))
    if summary["ambiguous"]:
        raise SystemExit("Ambiguous symbol/date matches: audit must be reviewed.")

if __name__ == "__main__":
    main()
