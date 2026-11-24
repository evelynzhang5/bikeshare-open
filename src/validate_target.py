"""Exercise 4: evaluate a daily-change target on H1 2012 only.

Run: python -m src.validate_target --source-commit <audited-commit>
The source commit is a provenance label; file hashes identify the actual code.
"""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import FORBIDDEN, RAW, ROOT, TARGET, TRAIN_END, VALID_END
from src.features import build_features, feature_columns
from src.ingest import load_raw
from src.train import MODELS, temporal_split
from src.validate_feature import sha256


def validation_data(raw):
    """Discard held-out dates before any feature construction."""
    allowed = raw.loc[raw.dteday <= pd.Timestamp(VALID_END)].copy()
    frame = build_features(allowed)
    train, valid, held_out = temporal_split(frame)
    if train.empty or valid.empty or not held_out.empty:
        raise ValueError("Expected training and validation rows, but no test rows")
    if not frame.dteday.is_unique or not frame.dteday.is_monotonic_increasing:
        raise ValueError("Feature dates must be unique and sorted")
    # This choice follows the separate cnt_roll_3 validation comparison.
    cols = [c for c in feature_columns(frame) if c != "cnt_roll_3"]
    if "cnt_lag_1" not in cols or set(cols) & FORBIDDEN:
        raise ValueError("Invalid input columns for a persistence-relative target")
    if not np.isfinite(frame[cols + [TARGET]]).all().all():
        raise ValueError("Non-finite inputs or targets")
    return train, valid, cols


def predict_daily_change(estimator, train, valid, cols):
    """Fit on past daily changes and return validation predictions in rides."""
    model = clone(estimator)
    change = train[TARGET] - train["cnt_lag_1"]
    model.fit(train[cols], change)
    return valid["cnt_lag_1"].to_numpy(dtype=float) + model.predict(valid[cols])


def run_validation(source_commit):
    started_at = datetime.now(timezone.utc).isoformat()
    pins = dict(
        line.split("==", 1)
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    for package in ("numpy", "pandas", "scikit-learn"):
        if version(package) != pins[package]:
            raise RuntimeError(f"Install pinned {package}=={pins[package]} first")

    train, valid, cols = validation_data(load_raw())
    predictions = {}
    for name, estimator in MODELS.items():
        model = clone(estimator)
        model.fit(train[cols], train[TARGET])
        predictions[name] = model.predict(valid[cols])
    predictions["hgb_daily_change"] = predict_daily_change(
        MODELS["hgb"], train, valid, cols
    )
    sources = ["requirements.txt", "src/config.py", "src/ingest.py",
               "src/features.py", "src/train.py", "src/validate_feature.py",
               "src/validate_target.py"]
    result = {
        "run_started_at_utc": started_at,
        "source_commit_label": source_commit,
        "source_sha256": {p: sha256(ROOT / p) for p in sources},
        "raw_sha256": sha256(RAW),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: version(p) for p in (
            "numpy", "pandas", "scikit-learn", "scipy", "joblib", "threadpoolctl"
        )},
        "scope": "2011 training / H1 2012 validation only",
        "train_end": TRAIN_END,
        "validation_end": VALID_END,
        "train_dates": [str(train.dteday.min().date()), str(train.dteday.max().date())],
        "valid_dates": [str(valid.dteday.min().date()), str(valid.dteday.max().date())],
        "n_train": len(train),
        "n_valid": len(valid),
        "n_features": len(cols),
        "features": cols,
        "excluded_candidate": "cnt_roll_3",
        "held_out_predictions": 0,
        "transformation": "z_d = cnt_d - cnt_lag_1_d",
        "reconstruction": "predicted_cnt_d = cnt_lag_1_d + predicted_z_d",
        "scoring_scale": "original daily ride counts",
        "negative_predictions_clipped": False,
        "tuning": "One specified transformation; original estimator parameters unchanged",
        "metrics": {
            name: {
                "r2": float(r2_score(valid[TARGET], pred)),
                "mae": float(mean_absolute_error(valid[TARGET], pred)),
            }
            for name, pred in predictions.items()
        },
    }
    prediction_rows = pd.DataFrame({"dteday": valid.dteday, "actual_cnt": valid[TARGET]})
    for name, pred in predictions.items():
        prediction_rows[name] = pred
    return result, prediction_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/evidence")
    args = parser.parse_args()
    result, prediction_rows = run_validation(args.source_commit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "exercise4-validation.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    prediction_rows.to_csv(args.output_dir / "exercise4-validation-predictions.csv", index=False)
    for name, score in result["metrics"].items():
        print(f"{name}: validation R2={score['r2']:.4f}, MAE={score['mae']:.1f}")
    print(f"OK target validation: {result['n_train']} train, {result['n_valid']} valid, "
          f"{result['n_features']} inputs; 0 held-out predictions")
