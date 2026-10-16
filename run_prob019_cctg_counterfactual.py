"""Read-only CCTG EMA counterfactual; never writes to R2."""
from __future__ import annotations
import hashlib, io, json, os
from pathlib import Path
import numpy as np
import pandas as pd

PERIODS = (20, 50, 150, 200)
SID = "KYG1993R1184"
CORRECTION_DATE = "2026-09-22"
CURRENT_KEY = f"history/ohlcv/{SID}.parquet"
RECOVERY_KEY = f"recovery/stooq-2026-09-25/history/ohlcv/{SID}.parquet"
OUT = Path("prob019_cctg_counterfactual.json")
REQUIRED = {"date", "security_id", "ticker", "adj_close"}


def normalize(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"{label} history missing columns: {sorted(missing)}")
    out = frame.copy()
    out["security_id"] = out["security_id"].astype(str)
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    out["adj_close"] = pd.to_numeric(out["adj_close"], errors="raise").astype(float)
    if out.duplicated(["security_id", "date"]).any():
        raise ValueError(f"{label} history has duplicate security/date rows")
    if not np.isfinite(out["adj_close"].to_numpy()).all() or (out["adj_close"] <= 0).any():
        raise ValueError(f"{label} history has invalid adjusted-close values")
    return out.sort_values("date").reset_index(drop=True)


def apply_counterfactual(current, recovery, security_id=SID, correction_date=CORRECTION_DATE):
    current, recovery = normalize(current, "current"), normalize(recovery, "recovery")
    date = pd.Timestamp(correction_date)
    cm = current["security_id"].eq(str(security_id)) & current["date"].eq(date)
    rm = recovery["security_id"].eq(str(security_id)) & recovery["date"].eq(date)
    if int(cm.sum()) != 1:
        raise ValueError(f"Expected exactly one current row for {security_id} on {correction_date}")
    if int(rm.sum()) != 1:
        raise ValueError(f"Expected exactly one recovery row for {security_id} on {correction_date}")
    before = float(current.loc[cm, "adj_close"].iloc[0])
    after = float(recovery.loc[rm, "adj_close"].iloc[0])
    out = current.copy()
    out.loc[cm, "adj_close"] = after
    return out, {"security_id": str(security_id), "date": correction_date,
                 "current_adj_close": before, "recovery_adj_close": after,
                 "changed": before != after}


def recursive_ema(history):
    prices = normalize(history, "EMA input")["adj_close"].astype(float).tolist()
    if not prices:
        raise ValueError("Cannot compute EMA from empty history")
    values = {p: prices[0] for p in PERIODS}
    for price in prices[1:]:
        for period in PERIODS:
            alpha = 2.0 / (period + 1.0)
            values[period] = alpha * price + (1.0 - alpha) * values[period]
    return {f"ema{p}": float(values[p]) for p in PERIODS}


def compare(calculated, shared_row):
    periods = {}
    for p in PERIODS:
        key = f"ema{p}"
        got, expected = float(calculated[key]), float(shared_row[key])
        passed = bool(np.isclose(got, expected, rtol=1e-8, atol=1e-8))
        periods[key] = {"calculated": got, "shared": expected,
                        "abs_error": abs(got - expected),
                        "relative_error": abs(got - expected) / abs(expected) if expected else None,
                        "passes_official_tolerance": passed}
    return {"periods": periods,
            "failed_periods": [k for k, v in periods.items() if not v["passes_official_tolerance"]],
            "passes_official_tolerance": all(v["passes_official_tolerance"] for v in periods.values())}


def main():
    from r2_ready import make_r2_client
    from shared_ema_state import load_shared_ema_state
    bucket = os.environ.get("R2_BUCKET_NAME", "ussy-data")
    s3 = make_r2_client()
    current_body = s3.get_object(Bucket=bucket, Key=CURRENT_KEY)["Body"].read()
    recovery_body = s3.get_object(Bucket=bucket, Key=RECOVERY_KEY)["Body"].read()
    current = normalize(pd.read_parquet(io.BytesIO(current_body)), "current")
    recovery = normalize(pd.read_parquet(io.BytesIO(recovery_body)), "recovery")
    shared, manifest = load_shared_ema_state()
    shared = shared.copy()
    shared["security_id"] = shared["security_id"].astype(str)
    rows = shared.loc[shared["security_id"].eq(SID)]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one shared EMA row for {SID}")
    shared_row = rows.iloc[0]
    as_of = pd.Timestamp(shared_row["as_of_date"]).tz_localize(None).normalize()
    current = current.loc[current["date"] <= as_of].copy()
    recovery = recovery.loc[recovery["date"] <= as_of].copy()
    if current.empty or pd.Timestamp(current["date"].max()).normalize() != as_of:
        raise ValueError(f"Current history does not reach shared EMA as-of date {as_of.date()}")
    counterfactual, row_change = apply_counterfactual(current, recovery)
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "governance": "READ_ONLY_R2_IN_MEMORY_COUNTERFACTUAL_NO_PRODUCTION_WRITES",
        "symbol": "CCTG", "security_id": SID, "as_of_date": str(as_of.date()),
        "current_history_key": CURRENT_KEY, "recovery_history_key": RECOVERY_KEY,
        "current_history_sha256": hashlib.sha256(current_body).hexdigest(),
        "recovery_history_sha256": hashlib.sha256(recovery_body).hexdigest(),
        "shared_ema_manifest": manifest, "official_tolerance": {"rtol": 1e-8, "atol": 1e-8},
        "counterfactual_row": row_change,
        "current_history": compare(recursive_ema(current), shared_row),
        "counterfactual_history": compare(recursive_ema(counterfactual), shared_row),
        "interpretation": "In-memory replacement only. A passing counterfactual supports the row as a sufficient explanation; it does not authorize or perform a production repair."
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
