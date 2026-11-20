# Peer repository audit

<!-- peer-audit:963defb18f395aef9368fcd41133d4e4d3ca7566:sha256:397b98771954e018fe1fed4a66691c749ad2df9625295c212117f6458a09e0ad -->
## Peer audit at 963defb

- Repository: [https://github.com/bothermeQAQ/bikeshare-open](https://github.com/bothermeQAQ/bikeshare-open)
- Reviewed commit: [`963defb18f395aef9368fcd41133d4e4d3ca7566`](https://github.com/bothermeQAQ/bikeshare-open/tree/963defb18f395aef9368fcd41133d4e4d3ca7566)
- Audit date: 2026-11-19, as stated in the captured report.
- Reviewer: the project's named `leakage-auditor`, invoked directly with `claude -p --agent leakage-auditor`; this was not a separately spawned subagent.
- Local model: `bikeshare-coder`; configured context: 65,536 tokens.
- Tool access: `Read`, `Grep`, and `Glob`; MCP tools were denied.
- Scope: static review of the peer checkout. No project code, tests, training, or scoring were executed for this review.
- Shell pipeline exit code reported by the student: `0` with `pipefail` enabled. This is completion evidence, not proof that the audit's conclusions are correct.
- Original temporary log: `/tmp/bikeshare-peer-audit-963defb.tNq2fS`.
- Preserved capture: [peer-audit-963defb-tNq2fS.txt](evidence/peer-audit-963defb-tNq2fS.txt).
- Capture SHA-256: `397b98771954e018fe1fed4a66691c749ad2df9625295c212117f6458a09e0ad`.

### Captured auditor output (verbatim)

The block below copies the complete saved stdout/stderr capture. The first two lines are CLI startup warnings. They are retained unchanged along with the model's report. Claims and numerical mistakes in the report have not been silently corrected.

````text
Permission deny rule (.claude/settings.json): Write(./data/raw/**) is not matched by file permission checks — only Edit(path) rules are. Use Edit(./data/raw/**) instead (Edit rules cover all file-editing tools).
[claude-code:unrecognized_model] {"model":"bikeshare-coder","query_source":"sdk"}
Based on my comprehensive static review of `/Users/evelynzhang/Downloads/bikeshare-peer-bothermeQAQ` against the five methodology checks, here is the complete report:

---

## Methodology Audit Report

**Repository:** `bikeshare-peer-bothermeQAQ`  
**Commit:** `963defb18f395aef9368fcd41133d4e4d3ca7566`  
**Date:** 2026-11-19

### Check 1: Target Leakage
**Status:** ✓ Pass

- **FORBIDDEN columns enforced in `src/config.py`:** `{casual, registered, cnt, instant, yr, days_since_2011, cnt_2d_bfr}`
- **`test_leakage_identity_holds`:** Verifies `casual + registered == cnt` exactly (line 20-22 of tests/test_leakage.py)
- **`feature_columns()` in `src/features.py` (line 82-85):** Filters out all FORBIDDEN columns before returning feature list
- **Lagged features:** All use `.shift(1)` or `.shift(LAG_WARMUP)` before aggregation
- **No affine identity leaks found** beyond the known sum: `casual + registered == cnt`

### Check 2: Temporal Ordering
**Status:** ✓ Pass

- **Temporal split by date only:** `src/train.py` temporal_split (lines 56-62) splits at `TRAIN_END = "2011-12-31"` and `VALID_END = "2012-06-30"`, never randomly
- **Model fit order:** `fit_and_score()` (line 77 in train.py) splits first, then fits only on train: `model.fit(train[cols], train[TARGET])`
- **Persistence baseline:** Uses only the `cnt_lag_1` column which is strictly past data; no fitting required

### Check 3: Calendar Gaps
**Status:** ✓ Pass

- **`reindex_to_calendar()` (line 34-50):** Expands df to contiguous calendar using `pd.date_range(..., freq="D")`, inserting NaN for missing days (including 2011-03-10)
- **Lag computation:** All `.shift()` operations run on the gap-filled index; subsequent `.dropna()` removes rows with NaN lags (the warmup period plus any gap-affected rows)
- **Test coverage:** `test_lags_are_true_calendar_lags` (line 34-43 of tests/test_leakage.py) verifies lag alignment across calendar days

### Check 4: Silent Row Loss
**Status:** ✓ Pass

- **`reindex_to_calendar()` adds explicit NaN for missing calendar days** — not row loss, but gap insertion
- **`dropna()` (line 79):** Removes only rows where lags are NaN (warmup period or gaps). Bounded implicitly by `LAG_WARMUP = 7` config value
- **No `.map()`, `.merge()`, or `.dropna()` without bounds:** The weather encoder (`encode_weather`) raises on unseen labels instead of silent drop; `dropna()` is only used after lag creation with documented warmup period

### Check 5: Unreported Baseline
**Status:** ✓ Pass

- **Both baselines reported:** `reports/metrics.json` includes both `baseline_mean` and `baseline_persistence` alongside ridge and hgb scores
- **Persistence baseline test R² = 0.5099**, MAE = 840.1 — within 0.07 R² of ridge, confirming the "yesterday again" baseline is meaningful
- **Mean baseline shows distribution shift costs** (valid: -0.9318, test: -2.1441)

---

## Verdict

**All five methodology checks pass.** No material findings requiring fixes.

The codebase correctly:
1. Prevents target leakage via FORBIDDEN filtering and explicit lag shifting
2. Enforces temporal ordering with date-based splits and train-only fitting
3. Handles calendar gaps via reindexing before lag computation
4. Avoids silent row loss — gap handling and warmup period are documented and tested
5. Reports both mean and persistence baselines alongside all model scores
````

### Reviewer verdict (ChatGPT-assisted)

The auditor reported no material findings. Static inspection supports the date-based splits, train-only fitted preprocessing, strictly historical demand features, calendar reindexing, and inclusion of both baselines, but its blanket pass needs qualification. The current untransformed Ridge test R² is 0.6238 versus persistence's 0.5099, a difference of 0.1139, not within 0.07; persistence still has lower MAE, 840.1 versus 876.6, by 36.5 rides per day. This corrects the audit's comparison, not the peer's committed scores. Row-loss protection comes from the explicit upper-bound assertion in tests/test_contract.py:28–43, not from LAG_WARMUP alone: src/features.py:79 applies dropna() to every column, so missing non-lag values could also remove rows. The peer reports seven initial losses and seven after the calendar gap; these counts were not reproduced in this review. The auditor's statement about affine identities is a static observation, not evidence that it performed a numerical identity search. Realized same-day weather is unavailable for a genuine day-ahead decision. REPORT.md already acknowledges this limitation, which the auditor omitted: an operational evaluation would need weather forecasts issued before prediction. That could change the model scores and deployment conclusion, but no numerical impact was measured here. No tests, training, or scoring were executed during this static audit or while preparing this assessment.

### Sources for the separate assessment

- [Committed untransformed scores](https://github.com/bothermeQAQ/bikeshare-open/blob/963defb18f395aef9368fcd41133d4e4d3ca7566/reports/metrics.json).
- [Feature construction and full-frame dropna](https://github.com/bothermeQAQ/bikeshare-open/blob/963defb18f395aef9368fcd41133d4e4d3ca7566/src/features.py#L53).
- [Explicit row-loss assertion](https://github.com/bothermeQAQ/bikeshare-open/blob/963defb18f395aef9368fcd41133d4e4d3ca7566/tests/test_contract.py#L28).
- [Training loop and preprocessing](https://github.com/bothermeQAQ/bikeshare-open/blob/963defb18f395aef9368fcd41133d4e4d3ca7566/src/train.py).
- [Peer report, including weather-availability limitation](https://github.com/bothermeQAQ/bikeshare-open/blob/963defb18f395aef9368fcd41133d4e4d3ca7566/REPORT.md).

### Attribution

The quoted report is the local auditor's actual saved output. ChatGPT checked the pinned source and committed metrics, drafted the separate assessment, and supplied this recording script. The student should review and revise the draft verdict before adopting it as their own assessment. Earlier attempts are not represented as this completed run.
