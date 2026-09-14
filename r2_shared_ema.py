"""Consume the governed canonical shared EMA(adj_close) state from ussy-data R2.

Production contract:
- pointer: production/indicators/ema/current.json
- immutable runs: production/indicators/ema/runs/
- price basis: adj_close
- periods: 20/50/150/200
- candidate -> equivalence -> immutable run -> pointer-last promotion

This module only replaces EMA facts on each security's terminal ready row. It does
not change Stage2, RS, breakout, ATR, volume, regime, or any other TrendFoll rule.
"""
from __future__ import annotations

import hashlib
import io
import json
import os

import numpy as np
import pandas as pd

from r2_ready import make_r2_client

EMA_POINTER_KEY = "production/indicators/ema/current.json"
EMA_RUN_PREFIX = "production/indicators/ema/runs/"
PROMOTION_POLICY = "candidate_then_equivalence_then_immutable_run_then_current_pointer_last_v1"
PRICE_BASIS = "adj_close"
PERIODS = (20, 50, 150, 200)
STATE_COLUMNS = ["security_id", "ticker", "as_of_date", "last_price", "ema20", "ema50", "ema150", "ema200"]


def _validate_state_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(STATE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Shared EMA state missing columns: {sorted(missing)}")
    state = frame[STATE_COLUMNS].copy()
    if state.empty:
        raise ValueError("Shared EMA state is empty")
    state["security_id"] = state["security_id"].astype(str)
    state["ticker"] = state["ticker"].astype(str)
    state["as_of_date"] = pd.to_datetime(state["as_of_date"], errors="raise").dt.tz_localize(None).dt.normalize()
    numeric = ["last_price", *(f"ema{p}" for p in PERIODS)]
    for column in numeric:
        state[column] = pd.to_numeric(state[column], errors="raise").astype("float64")
    if state["as_of_date"].isna().any() or state.duplicated("security_id").any():
        raise ValueError("Shared EMA state has invalid dates or duplicate security_id")
    if state.duplicated("ticker").any():
        raise ValueError("Shared EMA state has duplicate ticker mapping")
    if not np.isfinite(state[numeric].to_numpy()).all() or (state[numeric] <= 0).any().any():
        raise ValueError("Shared EMA state has invalid numeric values")
    return state.sort_values("security_id").reset_index(drop=True)


def load_shared_ema_state(s3=None, bucket: str | None = None):
    s3 = s3 or make_r2_client()
    bucket = bucket or os.environ.get("R2_BUCKET_NAME", "ussy-data")
    manifest = json.loads(s3.get_object(Bucket=bucket, Key=EMA_POINTER_KEY)["Body"].read())
    required = {
        "schema_version", "created_at", "price_basis", "periods", "securities",
        "parquet_key", "sha256", "source_ready_parquet_key", "source_ready_sha256",
        "update_method", "promotion_policy", "equivalence",
    }
    if not required.issubset(manifest):
        raise ValueError("Shared EMA manifest lacks required promotion evidence")
    key = manifest.get("parquet_key", "")
    if manifest.get("schema_version") != 1 or manifest.get("price_basis") != PRICE_BASIS:
        raise ValueError("Shared EMA manifest schema/price basis invalid")
    if list(manifest.get("periods", [])) != list(PERIODS) or not key.startswith(EMA_RUN_PREFIX):
        raise ValueError("Shared EMA manifest periods/key invalid")
    if manifest.get("promotion_policy") != PROMOTION_POLICY:
        raise ValueError("Shared EMA promotion policy is not approved")
    eq = manifest.get("equivalence")
    if not isinstance(eq, dict) or eq.get("numeric_failures") != 0 or eq.get("classification_mismatches") != 0:
        raise ValueError("Shared EMA equivalence gate did not pass")
    if not isinstance(eq.get("verified"), int) or eq["verified"] < 1:
        raise ValueError("Shared EMA equivalence coverage invalid")

    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if hashlib.sha256(body).hexdigest() != manifest.get("sha256"):
        raise ValueError("Shared EMA Parquet checksum mismatch")
    state = _validate_state_frame(pd.read_parquet(io.BytesIO(body), engine="pyarrow"))
    if len(state) != manifest.get("securities"):
        raise ValueError("Shared EMA manifest/data security count mismatch")
    security_ids = manifest.get("security_ids")
    if security_ids is not None and set(state["security_id"]) != set(map(str, security_ids)):
        raise ValueError("Shared EMA manifest/data security IDs mismatch")
    return state, manifest


def apply_shared_ema_terminal(features: pd.DataFrame, ready: pd.DataFrame, ready_manifest: dict, *, state=None, ema_manifest=None):
    """Replace terminal-row EMA facts with governed long-history recursive state.

    The terminal classification follows the canonical analytical basis exactly:
    adj_close > EMA20 > EMA50 > EMA150 > EMA200.
    """
    if state is None or ema_manifest is None:
        state, ema_manifest = load_shared_ema_state()
    state = _validate_state_frame(state)

    ready_key = ready_manifest.get("parquet_key")
    ready_sha = ready_manifest.get("sha256")
    if (ema_manifest.get("source_ready_parquet_key"), ema_manifest.get("source_ready_sha256")) != (ready_key, ready_sha):
        raise ValueError("Shared EMA state is not aligned with current ready dataset")

    ready_map = ready[["security_id", "ticker"]].drop_duplicates().copy()
    ready_map["security_id"] = ready_map["security_id"].astype(str)
    ready_map["ticker"] = ready_map["ticker"].astype(str)
    if ready_map.duplicated("security_id").any() or ready_map.duplicated("ticker").any():
        raise ValueError("Ready security/ticker mapping is not one-to-one")
    if set(state["security_id"]) != set(ready_map["security_id"]):
        raise ValueError("Shared EMA security set differs from ready security set")
    joined = state.merge(ready_map, on="security_id", suffixes=("_ema", "_ready"), validate="one_to_one")
    if not joined["ticker_ema"].eq(joined["ticker_ready"]).all():
        raise ValueError("Shared EMA ticker mapping differs from ready")

    out = features.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    terminal_idx = out.sort_values(["symbol", "date"]).groupby("symbol", sort=False).tail(1).index
    terminal = out.loc[terminal_idx, ["symbol", "date", "close_adj"]].copy()
    terminal = terminal.merge(
        state.rename(columns={"ticker": "symbol"}),
        on="symbol", how="left", validate="one_to_one",
    )
    if terminal["security_id"].isna().any():
        missing = terminal.loc[terminal["security_id"].isna(), "symbol"].tolist()
        raise ValueError(f"Shared EMA missing terminal symbols: {missing[:20]}")
    if not terminal["date"].eq(terminal["as_of_date"]).all():
        bad = terminal.loc[terminal["date"].ne(terminal["as_of_date"]), "symbol"].tolist()
        raise ValueError(f"Shared EMA as_of_date mismatch: {bad[:20]}")
    if not np.allclose(terminal["close_adj"].astype(float), terminal["last_price"].astype(float), rtol=1e-10, atol=1e-10):
        raise ValueError("Shared EMA last_price disagrees with terminal ready adj_close")

    state_by_symbol = terminal.set_index("symbol")
    for idx in terminal_idx:
        symbol = str(out.at[idx, "symbol"])
        row = state_by_symbol.loc[symbol]
        for period in PERIODS:
            out.at[idx, f"ema{period}"] = float(row[f"ema{period}"])
        out.at[idx, "ema_stack_aligned"] = bool(
            float(row["last_price"]) > float(row["ema20"]) > float(row["ema50"])
            > float(row["ema150"]) > float(row["ema200"])
        )

    report = {
        "price_basis": PRICE_BASIS,
        "terminal_rows_replaced": int(len(terminal_idx)),
        "state_securities": int(len(state)),
        "source_ready_lineage_match": True,
        "equivalence_verified": int(ema_manifest["equivalence"]["verified"]),
        "production_parquet_key": ema_manifest["parquet_key"],
    }
    return out, report
