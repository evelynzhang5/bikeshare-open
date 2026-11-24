# Bikeshare demand: forecasting and agent verification

## Results

The target is daily rides (`cnt`). Training uses 2011, validation H1 2012,
and test H2 2012. Calendar reindexing precedes all lags. The unchanged raw
file has 728 observations; 714 survive feature construction: 348 training,
182 validation, and 184 test. The 14 observed rows removed are seven initial
warmup days and seven days following the missing 2011-03-10. The full-frame
`dropna()` is protected by an explicit row-loss assertion; the lag-window
constant alone cannot prevent loss from unrelated missing values.

The **selected configuration is the original 14-input, untransformed Ridge**,
with train-fitted scaling and alpha=1.0. `cnt_roll_3` remains implemented and
tested but is excluded from that selection. The 15-input variant adds only
this feature. HGB keeps random_state=0 and max_iter=300. The selection and
fixed comparison were committed at
[`af4e096`](https://github.com/evelynzhang5/bikeshare-open/commit/af4e0962caddcb0bd8a824a1df5eaa33ee8935df)
before this final H2 scoring run. Earlier starter documentation and the peer
audit exposed example H2 results; I do not claim those scores were unknown.
Our feature and target-transformation comparisons used H1 only, followed by
one final run of the predetermined before/after configurations. No choice
changed after that run.

| Feature set | Method | Validation R² | Validation MAE | Test R² | Test MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| Before: 14 inputs | `baseline_mean` | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before: 14 inputs | `baseline_persistence` | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before: 14 inputs | `ridge` | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before: 14 inputs | `hgb` | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After: 15 inputs | `baseline_mean` | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After: 15 inputs | `baseline_persistence` | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After: 15 inputs | `ridge` | 0.6439 | 836.5 | 0.5800 | 946.2 |
| After: 15 inputs | `hgb` | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

MAE is rides per day. These are untransformed results from `make all`, matching
[metrics.json](reports/metrics.json) to the printed digit. All 32 values were
independently recalculated from the 366 saved validation/test prediction rows;
all eight H1 rows also match the earlier validation-only comparison. See the
[pipeline log](docs/evidence/final-pipeline.log),
[run manifest](docs/evidence/final-run.json), and
[verification log](docs/evidence/final-artifact-checks.log).
`python -m src.verify_results` repeats the artifact checks without fitting models.

These are sequential one-day predictions using observed previous counts,
not a six-month open-loop forecast. Realized same-day weather is also an input;
the results therefore describe a conditional benchmark, not demonstrated
operational day-ahead accuracy with weather forecasts available at issue time.

## Headline finding

Untransformed gradient boosting struggles with the shift to higher demand:
with the original features, test R² is **-0.4975** and MAE **1972.6**, while Ridge
reaches **0.5833** and **947.1**. Negative R² means HGB is worse under squared
error than the test-period constant mean; it still comfortably beats the
training-mean baseline (R² **-2.1441**, MAE **2847.7**). The training target mean
is 3493.5 rides versus 6042.9 in test; HGB's test predictions average 4233.3
and peak at 5537.0, whereas observed test demand reaches 8714. This is evidence
of underprediction consistent with difficulty adapting to growth, not proof
that every boosted ensemble is mathematically bounded by its training targets.
Ridge also must be judged against persistence: **0.5099** R² and **840.1** MAE
make yesterday's count a strong competitor, with lower absolute error.

Adding `cnt_roll_3` worsened validation R²/MAE for Ridge from 0.6475/832.9 to
0.6439/836.5 and for HGB from 0.2185/1296.6 to 0.1983/1311.6, so I retained its
implementation and failing-test history but dropped it from the selected model.

## Exercise 4: target transformation

The specified transformation was daily change,
`z_d = cnt_d - cnt_lag_1_d`; predicted demand is the known previous-day count
plus the predicted change. On the same 14 inputs and H1 validation rows,
HGB improved from R² **0.2185** / MAE **1296.6** to **0.6079** / **834.3**.
For context, the mean baseline was **-0.9318** / **2002.2**, persistence
**0.4507** / **900.6**, and Ridge **0.6475** / **832.9**. The transformed tree
became competitive on MAE but remained slightly worse than Ridge on both
metrics. Results and reconstruction checks are recorded in
[EXERCISE4_VALIDATION.md](docs/EXERCISE4_VALIDATION.md).

This is a defensible persistence-plus-correction model: yesterday's count is
known before predicting today, and today's observed count is used only as a
training target, never in reconstruction at prediction time. It accommodates
changes in demand level without asking the tree to predict the full level.
It would need recursive forecasts for horizons without observed previous
counts, and the realized-weather limitation still applies. One transformation
was evaluated with unchanged hyperparameters; no transformed H2 score was
computed. The committed final metrics remain untransformed, as required.

## Exercise 5: ridge vs persistence

I would not replace persistence with Ridge for deployment on this evidence.
For the selected configuration, Ridge gains **0.0734 R²** on H2 (0.5833 versus
0.5099) but increases MAE by **107.0 rides/day**, approximately **12.7%**
(947.1 versus 840.1). Higher R² means lower squared error and could matter if
large misses are disproportionately costly, but that cost objective has not
been established. For routine absolute-error performance, the simpler
persistence forecast wins. Ridge was better on H1 MAE (832.9 versus 900.6),
so the final comparison demonstrates that its validation advantage did not
transfer on that measure. This assessment leaves the frozen experimental
selection unchanged. Any operational model also needs evaluation with
weather forecasts available before prediction; the present benchmark does
not establish that deployment would improve service.

## Attribution

The local agent used **qwen3.5:9b-q4_K_M via Ollama as `bikeshare-coder`, with
a 65,536-token context**. The 9B nvfp4 variant was replaced by Q4_K_M after
high memory use. This was a configuration change, not a controlled comparison
of model sizes. ChatGPT/Codex also assisted with prompts, review, scripts,
validation and final computations, and this report; those parts were not all
generated by the local open-weight model.

**Agent-generated work:**

- The supplied starter provided the original pipeline, tests, permissions,
  hook, reviewer, and SDK auditor; it is not claimed as original student work.
- Local Claude Code produced the `cnt_roll_3` implementation and test,
  classification/weather checks, and temporary fault edits. The three Edit
  experiments and repairs are preserved in [SEEDED_FAULTS.md](docs/SEEDED_FAULTS.md).
- ChatGPT assisted with `/seed-fault`, evidence-recording scripts, and the peer
  assessment. The actual peer reviewer output and separate qualified verdict
  are preserved in [AUDIT.md](docs/AUDIT.md).
- Codex prepared `src/validate_feature.py`, `src/validate_target.py`, the frozen
  final comparison and prediction verification, the raw hash guard, SDK
  repairs, and this report draft. Actual outputs are committed, not reconstructed.

**Methodological decisions retained for this submission, with AI assistance:**

- Predict daily total rides; exclude same-day count components, unverified
  shipped lags, and raw time indexes; use chronological splits and both
  baselines (the five original entries in [DECISIONS.md](docs/DECISIONS.md)).
- Accept only strictly historical, calendar-aligned demand features; retain
  the test-first implementation but exclude `cnt_roll_3` from the selected
  model because validation worsened (November 17, 23, and 24 entries).
- Evaluate one daily-change transformation on validation, reconstruct counts
  using only the known lag, and retain the untransformed final comparison
  (November 23 and 24 entries).
- Freeze the 14-input Ridge before final scoring, then report its deployment
  limitations honestly, including the persistence MAE advantage and unavailable
  realized weather (November 24 entries).

Verification before final scoring recorded **24 passing tests**. The fourth
Bash-copy experiment was blocked before execution; it is documented as a
blocked attempt, not a demonstrated hook bypass. A later ingestion SHA-256
guard and temporary-copy test add protection without altering that history.
The required own-repository SDK audit remains pending on the Mac's local
Ollama endpoint. No `reports/audit.jsonl` is fabricated here: after `make audit`,
its actual findings must be addressed or explained in this report before
submission. The student must review and adopt the methodological verdicts
and this AI-assisted draft.
