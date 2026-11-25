"""The tests that make the agent honest.

test_no_forbidden_features is the single most valuable test in this repo:
casual + registered == cnt exactly, so any model handed those columns
scores R^2 = 1.0 and looks brilliant while having learned nothing.
"""
from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from src.config import FORBIDDEN, LEAKAGE_COLS, TARGET
from src.features import build_features, feature_columns, encode_weather
from src.ingest import load_raw


@pytest.fixture(scope="module")
def feats():
    return build_features(load_raw())


def test_leakage_identity_holds(feats):
    """Documents *why* casual and registered are forbidden."""
    assert (feats.casual + feats.registered == feats[TARGET]).all()


def test_no_forbidden_features(feats):
    """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
    construction, so this cannot discover a *new* leaky column. What it
    catches is someone editing feature_columns() or FORBIDDEN -- which is
    exactly the fault the Step 7 hook demonstrates."""
    cols = set(feature_columns(feats))
    assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"


def test_lags_are_true_calendar_lags(feats):
    """cnt_lag_1 for date d must equal cnt on d-1, in calendar days."""
    by_date = feats.set_index("dteday")[TARGET]
    checked = 0
    for date, lag in feats.set_index("dteday").cnt_lag_1.items():
        prev = date - pd.Timedelta(days=1)
        if prev in by_date.index:
            assert lag == pytest.approx(by_date[prev]), f"bad lag at {date.date()}"
            checked += 1
    assert checked > 600, "too few rows actually verified"


def test_lag_is_not_the_target(feats):
    assert not (feats.cnt_lag_1 == feats[TARGET]).all()


def test_rolling_mean_excludes_today(feats):
    """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
    by_date = feats.set_index("dteday")[TARGET]
    date = feats.dteday.iloc[200]
    window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
    if all(d in by_date.index for d in window):
        expected = sum(by_date[d] for d in window) / 7
        assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)


def test_no_missing_values(feats):
    assert feats[feature_columns(feats)].isna().sum().sum() == 0


def test_dates_are_sorted_and_unique(feats):
    assert feats.dteday.is_monotonic_increasing
    assert feats.dteday.is_unique


def test_cnt_roll_3_uses_only_previous_days(feats):
    assert "cnt_roll_3" in feats.columns, "cnt_roll_3 has not been implemented"
    by_date = feats.set_index("dteday")
    # Raw counts: July 12 = 4258, July 13 = 4342, July 14 = 5084.
    expected = (4258 + 4342 + 5084) / 3
    actual = by_date.loc[pd.Timestamp("2011-07-15"), "cnt_roll_3"]
    assert actual == pytest.approx(expected)


def test_unknown_weather_label_raises():
    labels = pd.Series(["GOOD", "MISTY", "BAD", "UNEXPECTED"])
    with pytest.raises(ValueError, match="unmapped weather labels"):
        encode_weather(labels)


def test_features_do_not_reconstruct_same_day_counts(feats):
    """Catch renamed, rescaled, or combined copies of unavailable same-day counts.

    Inspect actual numeric values, including combinations of up to three inputs.
    This bounds the check; it is not a proof against arbitrary nonlinear leaks.
    """
    columns = feature_columns(feats)
    forbidden_targets = sorted(LEAKAGE_COLS)
    values = feats[columns].to_numpy(dtype=float)
    targets = feats[forbidden_targets].to_numpy(dtype=float)
    for size in range(1, min(3, len(columns)) + 1):
        for positions in combinations(range(len(columns)), size):
            design = np.column_stack([values[:, positions], np.ones(len(feats))])
            coefficients, *_ = np.linalg.lstsq(design, targets, rcond=None)
            residual = np.abs(design @ coefficients - targets).max(axis=0)
            reconstructed = [
                name for name, error in zip(forbidden_targets, residual)
                if error < 1e-6
            ]
            names = [columns[position] for position in positions]
            assert not reconstructed, (
                f"inputs {names} reconstruct unavailable same-day counts: {reconstructed}"
            )
