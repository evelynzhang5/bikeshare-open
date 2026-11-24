# Exercise 4: daily-change target on validation data

Run date: 2026-11-23 (America/Los_Angeles). Source base:
[`f9277f13dec8e7ed4ff771773f0ec1aa1fb13996`](https://github.com/evelynzhang5/bikeshare-open/tree/f9277f13dec8e7ed4ff771773f0ec1aa1fb13996).

The target transformation substantially improves the tree model. Its MAE becomes
close to Ridge's, but Ridge still performs better on both validation metrics.
This experiment is complete on validation data; final held-out results and the
full assignment report remain separate work.

| Model | Validation R² | Validation MAE (rides/day) |
| --- | ---: | ---: |
| Training-mean baseline | -0.9318 | 2002.2 |
| Persistence baseline | 0.4507 | 900.6 |
| Ridge, original target | 0.6475 | 832.9 |
| HGB, original target | 0.2185 | 1296.6 |
| HGB, daily-change target | 0.6079 | 834.3 |

Unrounded differences: the transformation increases HGB R² by 0.3894738 and
reduces its MAE by 462.3071 rides/day. Its MAE remains 1.3657 above Ridge's.
These are descriptive results on one validation period, not a significance test.

## Transformation and availability

For date d, define the training label as `z_d = cnt_d - cnt_lag_1_d`.
Fit the same HGB estimator to this label using the original 14 model inputs.
Convert its validation output back to ride counts using
`predicted_cnt_d = cnt_lag_1_d + predicted_z_d` before computing R² or MAE.
No clipping or other post-processing was applied.

The transformation is defensible because yesterday's count is already available
when predicting today. It does not need today's observed target, a future growth
factor, or a trend estimated from validation or test labels. Calendar reindexing
and shifting in the existing feature builder determine the lag. The daily-change
labels are fitted only on 2011 observations.

This changes the model into persistence plus a learned correction. The known lag
provides a changing demand level outside the tree, so the model can adapt to a
higher level of ridership without asking the tree alone to learn the entire
level from 2011. It is therefore a different model parameterization, and these
results do not show that the original tree model was already competitive.

The evaluation assumes sequential one-day predictions: counts from earlier
validation dates become available before later dates are predicted. It is not a
forecast of all six months issued at the end of 2011. The existing same-day
weather measurements also remain a limitation; real day-ahead deployment needs
weather forecasts available at prediction time. No operational or held-out
performance was measured here. The corrected tree remains behind Ridge, so there
is no validation basis in this comparison to prefer it over Ridge.

## Fixed experimental choices

- One transformation was specified before this run: change from yesterday.
  No further transformations or hyperparameters were searched after seeing the result.
- Use the original 14 inputs, based on the prior `cnt_roll_3` ablation. The
  feature implementation and its test remain in the repository.
- Train on 348 eligible rows in 2011; evaluate on 182 dates from 2012-01-01
  through 2012-06-30. All five methods use identical rows and inputs.
- The runner filters away H2 rows before feature construction, calls the original
  `temporal_split`, and verifies that its test frame is empty.
- Fit independent clones of the existing model definitions. StandardScaler is
  fitted only on training data. HGB retains max_iter=300 and random_state=0.
- Use the pinned NumPy 2.5.3, pandas 3.0.5, and scikit-learn 1.9.1 versions
  in a cloud Linux environment with Python 3.12.14. Other numeric-package
  versions and source/data hashes are in the JSON evidence.
- Original feature building, model definitions, raw data, and existing tests
  are unchanged. The standard training pipeline and `reports/metrics.json`
  are not modified by this experiment.

## Actual commands and evidence

The comparison command completed with exit code 0:

```bash
set -o pipefail
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv-validation/bin/python -m src.validate_target --source-commit f9277f13dec8e7ed4ff771773f0ec1aa1fb13996 2>&1 | tee docs/evidence/exercise4-validation.log
```

In an activated project environment with the pinned requirements, replace
`.venv-validation/bin/python` with `python`. The source-commit argument labels
the base; the saved hashes identify the actual computation files.

- [Complete command output](evidence/exercise4-validation.log)
- [Full-precision metrics and provenance](evidence/exercise4-validation.json)
- [All 182 validation targets and predictions](evidence/exercise4-validation-predictions.csv)
- [Runner](../src/validate_target.py)

The following selected checks were run before the experiment:

```bash
set -o pipefail
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv-validation/bin/python -m pytest -q --color=no tests/test_target_validation.py tests/test_leakage.py tests/test_contract.py::test_calendar_is_complete_before_lagging tests/test_contract.py::test_only_expected_rows_are_dropped tests/test_contract.py::test_raw_columns_are_classified 2>&1 | tee docs/evidence/exercise4-checks.log
```

Result: 15 passed in 1.33s, exit code 0. The three new checks verify reconstruction
in ride counts, independence from validation targets at prediction time, and
exclusion of H2 rows before feature construction. Existing structural tests use
their original full-data fixtures, without forecasting on H2. The forecasting
test that scores H2 and the full Make targets were not run.

- [Complete test output](evidence/exercise4-checks.log)
- [Additional artifact verification](evidence/exercise4-artifact-checks.log)

The artifact verification recalculated every metric directly from the saved CSV,
checked all dates, matched the original four model rows exactly to the earlier
14-input run, and verified the recorded source and raw-data hashes. It did not
refit any models. The three new tests are in
[`tests/test_target_validation.py`](../tests/test_target_validation.py).

## Attribution

ChatGPT/Codex suggested the transformation, wrote the runner and checks, executed
them in the cloud, and drafted this interpretation. The output logs, metrics, and
predictions are from the actual run. This work did not use the local open-weight
model and should be identified separately in the final Attribution section.
