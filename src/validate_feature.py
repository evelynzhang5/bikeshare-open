"""Compare an added feature on validation data only.

Run from the repository root:
    python -m src.validate_feature --source-commit <audited-commit>

The commit is a provenance label; the source and data hashes below identify
the files actually used. This command never invokes src.train.fit_and_score.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import FORBIDDEN, RAW, ROOT, TARGET, TRAIN_END, VALID_END
from src.features import build_features, feature_columns
from src.ingest import load_raw
from src.train import MODELS, temporal_split


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(feature, source_commit):
    # Verify the three packages that define the numeric/model computation.
    pins = dict(
        line.split("==", 1)
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    for name in ("numpy", "pandas", "scikit-learn"):
        if version(name) != pins[name]:
            raise RuntimeError(f"Install the pinned {name}=={pins[name]} first")

    # Exclude H2 2012 before feature construction. No test predictions exist.
    raw = load_raw()
    raw = raw.loc[raw.dteday <= pd.Timestamp(VALID_END)].copy()
    frame = build_features(raw)
    train, valid, held_out = temporal_split(frame)
    if len(held_out) or train.empty or valid.empty:
        raise RuntimeError("Expected nonempty train/validation and no test rows")
    if not (train.dteday.max() < valid.dteday.min()):
        raise RuntimeError("Training and validation dates overlap")
    if not frame.dteday.is_unique or not frame.dteday.is_monotonic_increasing:
        raise RuntimeError("Feature dates must be unique and ordered")

    cols = feature_columns(frame)
    if feature not in cols or feature == "cnt_lag_1":
        raise ValueError("Candidate must be an included, non-persistence feature")
    if set(cols) & FORBIDDEN or not np.isfinite(frame[cols]).all().all():
        raise RuntimeError("Forbidden or non-finite model inputs")

    sources = ["requirements.txt", "src/config.py", "src/ingest.py",
               "src/features.py", "src/train.py", "src/validate_feature.py"]
    result = {
        "scope": "2011 training / H1 2012 validation only",
        "source_commit_label": source_commit,
        "source_sha256": {p: sha256(ROOT / p) for p in sources},
        "raw_sha256": sha256(RAW),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: version(p) for p in (
            "numpy", "pandas", "scikit-learn", "scipy", "joblib", "threadpoolctl"
        )},
        "candidate_feature": feature,
        "train_end": TRAIN_END,
        "validation_end": VALID_END,
        "n_raw_before_validation_end": len(raw),
        "n_feature_rows": len(frame),
        "n_train": len(train),
        "n_valid": len(valid),
        "train_dates": [str(train.dteday.min().date()), str(train.dteday.max().date())],
        "valid_dates": [str(valid.dteday.min().date()), str(valid.dteday.max().date())],
        "held_out_predictions": 0,
        "evaluation": "Sequential one-day prediction with observed prior-day counts",
        "weather_limit": "Realized same-day weather; not an operational day-ahead weather forecast",
        "variants": {},
    }
    # The same complete rows are used for both variants. The 7-day history
    # already required by cnt_roll_7 also supplies the 3-day candidate history.
    for variant, features in (
        ("without_feature", [c for c in cols if c != feature]),
        ("with_feature", cols),
    ):
        entry = {"n_features": len(features), "features": features, "metrics": {}}
        for name, original in MODELS.items():
            model = clone(original)
            model.fit(train[features], train[TARGET])
            predictions = model.predict(valid[features])
            entry["metrics"][name] = {
                "r2": float(r2_score(valid[TARGET], predictions)),
                "mae": float(mean_absolute_error(valid[TARGET], predictions)),
            }
        result["variants"][variant] = entry
    for baseline in ("baseline_mean", "baseline_persistence"):
        before = result["variants"]["without_feature"]["metrics"][baseline]
        after = result["variants"]["with_feature"]["metrics"][baseline]
        if before != after:
            raise RuntimeError(f"Baseline changed across identical rows: {baseline}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", default="cnt_roll_3")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/evidence/validation-cnt-roll-3.json")
    args = parser.parse_args()
    results = compare(args.feature, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    for label, entry in results["variants"].items():
        print(f"{label}: {entry['n_features']} features")
        for name, metrics in entry["metrics"].items():
            print(f"  {name}: validation R2={metrics['r2']:.4f}, MAE={metrics['mae']:.1f}")
    print(f"OK validation: {results['n_train']} train, {results['n_valid']} valid; "
          f"0 held-out predictions -> {args.output.name}")
