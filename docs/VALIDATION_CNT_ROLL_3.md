# Validation comparison for `cnt_roll_3`

Run date: 2026-11-19 (America/Los_Angeles).

Adding the three-day historical demand average did not improve either existing
model on H1 2012. This is a validation result, not a held-out test result or a
statistical significance claim.

| Model | R² without | R² with | MAE without | MAE with |
| --- | ---: | ---: | ---: | ---: |
| Training-mean baseline | -0.9318 | -0.9318 | 2002.2 | 2002.2 |
| Persistence baseline | 0.4507 | 0.4507 | 900.6 | 900.6 |
| Ridge | 0.6475 | 0.6439 | 832.9 | 836.5 |
| HistGradientBoosting | 0.2185 | 0.1983 | 1296.6 | 1311.6 |

MAE is measured in rides per day. Differences calculated before rounding are:

- Ridge: R² decreased by 0.0036385; MAE increased by 3.5490.
- HistGradientBoosting: R² decreased by 0.0202049; MAE increased by 14.9810.

Recommendation: use the original 14 inputs for the eventual model selection
comparison, while retaining the implemented feature and its test-first evidence.
This experiment does not change the project's default feature selection or choose
a target transformation. It also does not evaluate H2 2012.

## Design and provenance

- Source: [evelynzhang5/bikeshare-open at 896052f](https://github.com/evelynzhang5/bikeshare-open/tree/896052fd30106de7ae7b6efe0f20a780dffb55d1).
- The 14 downloaded original files, including raw data and the relevant source
  and tests, were verified against their Git blob hashes before and after this
  run. Existing source, tests, model definitions, and raw data were unchanged.
- Raw CSV SHA-256: `a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc`.
- Execution: a separate cloud Linux environment, Python 3.12.14. No local Claude
  or Ollama inference was used to fit the forecasting models.
- Pinned numeric packages: NumPy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1. Exact
  transitive numeric-package versions are recorded in the JSON evidence.
- Training: 348 eligible rows, 2011-01-10 through 2011-12-31.
- Validation: 182 rows, 2012-01-01 through 2012-06-30.
- The runner filters the raw frame to dates through `VALID_END` before feature
  construction, then uses `src.train.temporal_split`. Its held-out frame is empty.
- Both variants use identical eligible rows. `cnt_roll_7` already requires the
  complete historical window needed by `cnt_roll_3`.
- Feature lists come from `feature_columns`; the only input difference is
  removing `cnt_roll_3` in the 14-feature variant.
- Estimators are independent clones of the existing `MODELS` definitions. Ridge
  includes train-fitted StandardScaler and alpha=1.0; HGB retains max_iter=300
  and random_state=0. Both baselines are included for both variants.
- No target transformation or hyperparameter search was performed. The existing
  `fit_and_score()` function was not called because it also scores the test set.

## Actual execution evidence

The comparison command executed successfully with shell exit code 0:

```bash
set -o pipefail
mkdir -p docs/evidence
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv-validation/bin/python -m src.validate_feature --source-commit 896052fd30106de7ae7b6efe0f20a780dffb55d1 2>&1 | tee docs/evidence/validation-cnt-roll-3.log
```

- [Complete captured comparison output](evidence/validation-cnt-roll-3.log)
- [Full-precision metrics, feature lists, versions, and source hashes](evidence/validation-cnt-roll-3.json)
- [Reusable validation runner](../src/validate_feature.py)

The existing structural checks were then run in the same pinned environment:

```bash
set -o pipefail
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv-validation/bin/python -m pytest -q --color=no tests/test_leakage.py tests/test_contract.py::test_calendar_is_complete_before_lagging tests/test_contract.py::test_only_expected_rows_are_dropped tests/test_contract.py::test_raw_columns_are_classified 2>&1 | tee docs/evidence/validation-guards.log
```

Result: 12 passed in 2.20s, exit code 0. See the
[complete test output](evidence/validation-guards.log). These structural tests use
their original full-data fixtures but do not train or score forecasting models.
The forecasting test `test_beats_the_mean_baseline`, which scores H2, was excluded.
Neither `make test`, `make train`, nor `make all` was run.

For reproduction in the project's activated environment, replace
`.venv-validation/bin/python` with `python` after installing the existing pinned
requirements. The commit argument is a provenance label; compare the recorded
source hashes as well when reproducing a result.

## Interpretation and limits

Validation uses observed demand from earlier validation dates when predicting
later dates, corresponding to sequential one-day predictions. This is not a
multi-month forecast issued on 2011-12-31. Calendar reindexing preserves calendar
lag meanings across missing days.

Realized same-day weather is included in both variants. The comparison is
therefore conditional on observed weather; genuine day-ahead use requires
weather forecasts available before prediction. No numerical deployment impact
was measured here.

The recommendation concerns this fixed split and the current model definitions.
It does not establish that a three-day average is universally unhelpful. Final
H2 scoring remains a separate step after the feature and transformation decisions
are fixed.

## Attribution

ChatGPT/Codex wrote the validation runner, executed the comparison and selected
structural checks on the verified source snapshot, and drafted this assessment.
The logs and JSON are actual execution outputs. This is separate from the earlier
local open-weight auditor's output.
