# Bikeshare demand capstone

Daily Capital Bikeshare counts, 2011-2012. We forecast `cnt` (total daily
rides) from calendar, weather, and lagged-demand features.

## Commands
- `make data` - download raw CSV and assert its shape
- `make features` - build `data/processed/features.parquet`
- `make train` - fit models, write `reports/metrics.json`
- `make test` - pytest; run this before claiming anything works
- `make all` - the three pipeline stages in order

## Non-negotiable rules
- **Never** put `casual` or `registered` in a feature set:
  `casual + registered == cnt` exactly. `src/config.py` lists these and the
  other excluded columns (`cnt_2d_bfr`, raw time indexes) with the reason
  for each. Derive feature lists from `FORBIDDEN`; never hand-type them.
  Renaming, rescaling, or combining same-day counts does not make them valid inputs.
- **Never** split this data randomly. Use `src.train.temporal_split`.
  Train = 2011, valid = H1 2012, test = H2 2012. Never tune on test.
- Any new lag or rolling feature must be built on a gap-free calendar
  index (`src.features.reindex_to_calendar`) and must `.shift(1)` before
  it aggregates. Add a test for it in `tests/test_leakage.py`.
- Report the mean baseline **and** the persistence baseline (yesterday's
  count) alongside every model. A negative R^2 is a finding, not a bug
  to hide.

## Style
- Standard library, pandas, scikit-learn only. No new dependencies
  without asking. Versions are pinned in `requirements.txt`.
- Modules are runnable: `python -m src.<module>` prints a one-line `OK ...`
  summary.
- Paths and constants live in `src/config.py`. Nothing is hardcoded twice.

## Gotchas
- The mirror in `DATA_URL` is missing 2011-03-10. It is NOT the UCI file:
  728 rows from 2011-01-03, not 731 from 2011-01-01.
- `weather` uses the labels `GOOD` / `MISTY` / `BAD`, not the UCI codes 1-4.
- Inspect growth and forecast errors; do not assume a boosted ensemble has
  the strict training-target range bound of a single regression tree.
- 2012-10-29 (Hurricane Sandy, 22 rides) is in the test set. Expect it in
  any residual plot.

## Fault experiments
- `/seed-fault forbidden|rolling|weather` demonstrates one temporary fault, records real evidence, and restores the original code.

## Validation experiments
- `python -m src.validate_target --source-commit <sha>` evaluates daily-change targets on H1 only.
- Reconstruct demand using the known `cnt_lag_1` before scoring; never use today's observed count for reconstruction.
- Freeze feature and transformation choices before final H2 evaluation; keep committed pipeline metrics untransformed.
- The selected configuration is the original 14-input Ridge; report both ablations without revising selection from test scores.
- Quality tests use H1; `make all` generates the frozen final validation/test comparison and prediction evidence.
- `make data` checks the canonical raw-file SHA-256, including after writes made outside Edit/Write hooks.
