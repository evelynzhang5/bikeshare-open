"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train
"""
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import (
    ABLATION_FEATURE, METRICS, PREDICTIONS, PROCESSED, SELECTED_FEATURE_SET,
    SELECTED_MODEL, TARGET, TRAIN_END, VALID_END,
)
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    """Prespecified before/after comparison, independent of held-out scores."""
    columns = feature_columns(df)
    if ABLATION_FEATURE not in columns:
        raise ValueError(f"required ablation feature missing: {ABLATION_FEATURE}")
    return {
        "before_feature": [c for c in columns if c != ABLATION_FEATURE],
        "after_feature": columns,
    }


def fit_and_score(*, save_predictions: bool = False) -> dict:
    df = pd.read_parquet(PROCESSED)
    train, valid, test = temporal_split(df)
    results = {
        "selected_feature_set": SELECTED_FEATURE_SET,
        "selected_model": SELECTED_MODEL,
        "target_transformation": "none",
    }
    predictions = pd.concat([valid, test])[["dteday", TARGET]].copy()
    predictions["split"] = "test"
    predictions.loc[valid.index, "split"] = "valid"
    for variant, cols in feature_sets(df).items():
        entry = {
            "n_features": len(cols), "features": cols,
            "n_train": len(train), "n_valid": len(valid), "n_test": len(test),
        }
        for name, estimator in MODELS.items():
            model = clone(estimator)
            model.fit(train[cols], train[TARGET])
            entry[name] = {}
            for split, part in [("valid", valid), ("test", test)]:
                pred = model.predict(part[cols])
                predictions.loc[part.index, f"{variant}__{name}"] = pred
                entry[name][split] = {
                    "r2": round(float(r2_score(part[TARGET], pred)), 4),
                    "mae": round(float(mean_absolute_error(part[TARGET], pred)), 1),
                }
        results[variant] = entry
    if save_predictions:
        PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(PREDICTIONS, index=False)
    return results


if __name__ == "__main__":
    res = fit_and_score(save_predictions=True)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(res, indent=2) + "\n")
    for variant in ("before_feature", "after_feature"):
        for name in MODELS:
            print(variant, name, json.dumps(res[variant][name]))
    print(f"OK train: 8 untransformed model rows -> {METRICS.name}")
