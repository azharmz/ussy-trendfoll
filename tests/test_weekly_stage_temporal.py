import inspect
import unittest

import pandas as pd

from feature_engine import compute_weekly_stage_features


class WeeklyStageTemporalTests(unittest.TestCase):
    def test_production_function_is_wfri_resampled(self):
        source = inspect.getsource(compute_weekly_stage_features)
        self.assertIn('resample("W-FRI").last()', source)

    def test_mon_thu_cannot_observe_current_friday_bucket(self):
        daily = pd.DataFrame({
            "date": pd.to_datetime([
                "2026-08-28",  # prior Friday
                "2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04",
            ]),
            "close_raw": [100.0, 101.0, 102.0, 103.0, 104.0, 999.0],
        })
        weekly = (
            daily.set_index("date")["close_raw"]
            .resample("W-FRI").last()
            .rename("weekly_close")
            .reset_index()
        )
        merged = pd.merge_asof(
            daily[["date"]].sort_values("date"),
            weekly.sort_values("date"),
            on="date",
            direction="backward",
        )
        for date in pd.to_datetime(["2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03"]):
            value = merged.loc[merged["date"] == date, "weekly_close"].iloc[0]
            self.assertEqual(value, 100.0)
        self.assertEqual(
            merged.loc[merged["date"] == pd.Timestamp("2026-09-04"), "weekly_close"].iloc[0],
            999.0,
        )

    def test_friday_holiday_labels_thursday_close_to_friday_without_early_visibility(self):
        # Good Friday 2026-04-03: no Friday session. W-FRI labels the weekly
        # aggregate 2026-04-03 even though the last observation is Thursday.
        daily = pd.DataFrame({
            "date": pd.to_datetime([
                "2026-03-27", "2026-03-30", "2026-03-31", "2026-04-01", "2026-04-02",
                "2026-04-06",
            ]),
            "close_raw": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        })
        weekly = (
            daily.set_index("date")["close_raw"]
            .resample("W-FRI").last()
            .rename("weekly_close")
            .reset_index()
        )
        holiday_week = weekly.loc[weekly["date"] == pd.Timestamp("2026-04-03")].iloc[0]
        self.assertEqual(holiday_week["weekly_close"], 104.0)

        merged = pd.merge_asof(
            daily[["date"]].sort_values("date"),
            weekly.sort_values("date"),
            on="date",
            direction="backward",
        )
        # On Thu Apr-02 the Apr-03-labelled bucket is still in the future, so
        # backward as-of correctly exposes only the prior completed Friday.
        self.assertEqual(
            merged.loc[merged["date"] == pd.Timestamp("2026-04-02"), "weekly_close"].iloc[0],
            100.0,
        )
        # On Mon Apr-06 the holiday-week bucket is now prior and becomes visible.
        self.assertEqual(
            merged.loc[merged["date"] == pd.Timestamp("2026-04-06"), "weekly_close"].iloc[0],
            104.0,
        )

    def test_monday_holiday_does_not_shift_week_label_or_use_future_rows(self):
        # Labor Day 2026-09-07: week starts Tuesday but remains labelled Friday.
        daily = pd.DataFrame({
            "date": pd.to_datetime([
                "2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11",
            ]),
            "close_raw": [100.0, 101.0, 102.0, 103.0, 104.0],
        })
        weekly = (
            daily.set_index("date")["close_raw"]
            .resample("W-FRI").last()
            .rename("weekly_close")
            .reset_index()
        )
        self.assertEqual(
            weekly.loc[weekly["date"] == pd.Timestamp("2026-09-11"), "weekly_close"].iloc[0],
            104.0,
        )
        merged = pd.merge_asof(
            daily[["date"]].sort_values("date"), weekly.sort_values("date"),
            on="date", direction="backward",
        )
        for date in pd.to_datetime(["2026-09-08", "2026-09-09", "2026-09-10"]):
            self.assertEqual(
                merged.loc[merged["date"] == date, "weekly_close"].iloc[0], 100.0
            )


if __name__ == "__main__":
    unittest.main()
