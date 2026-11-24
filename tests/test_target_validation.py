"""Checks for the validation-only daily-change experiment; no test-set scoring."""
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor

from src import validate_target


def test_change_predictions_are_reconstructed_in_ride_counts():
    train = pd.DataFrame({"cnt": [100, 150, 170], "cnt_lag_1": [90, 110, 150]})
    valid = pd.DataFrame({"cnt": [180, 230], "cnt_lag_1": [170, 200]})
    estimator = DummyRegressor(strategy="mean")
    actual = validate_target.predict_daily_change(estimator, train, valid, ["cnt_lag_1"])
    # Training changes are 10, 40, 20. Add their mean to each known past count.
    assert actual == pytest.approx([170 + 70 / 3, 200 + 70 / 3])
    assert not hasattr(estimator, "constant_"), "Experiment must fit an independent clone"


def test_validation_targets_do_not_influence_change_predictions():
    train = pd.DataFrame({"cnt": [100, 150], "cnt_lag_1": [90, 110]})
    valid = pd.DataFrame({"cnt": [180, 230], "cnt_lag_1": [170, 200]})
    estimator = DummyRegressor(strategy="mean")
    expected = validate_target.predict_daily_change(estimator, train, valid, ["cnt_lag_1"])
    valid["cnt"] = [-1e12, 1e12]
    actual = validate_target.predict_daily_change(estimator, train, valid, ["cnt_lag_1"])
    assert actual == pytest.approx(expected)


def test_held_out_rows_never_reach_feature_builder(monkeypatch):
    raw = pd.DataFrame({
        "dteday": pd.to_datetime(["2011-12-31", "2012-06-30", "2012-07-01"]),
        "cnt": [100, 120, 999999],
        "cnt_lag_1": [90, 110, 120],
        "cnt_roll_3": [80, 100, 110],
    })

    def checked_builder(frame):
        assert frame.dteday.tolist() == [pd.Timestamp("2011-12-31"), pd.Timestamp("2012-06-30")]
        return frame.copy()

    monkeypatch.setattr(validate_target, "build_features", checked_builder)
    train, valid, cols = validate_target.validation_data(raw)
    assert len(train) == len(valid) == 1
    assert cols == ["cnt_lag_1"]
