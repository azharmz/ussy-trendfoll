"""Deprecated compatibility import.

No feature formulas live here. New code must import build_feature_store_from_r2
from r2_integration. Remove this shim after remaining research/audit consumers
have migrated.
"""
from r2_integration import build_feature_store_from_r2

__all__ = ["build_feature_store_from_r2"]
