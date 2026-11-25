# Seeded Faults and Test-First Evidence

## New feature: failing-test evidence

This test-first evidence is separate from the four required seeded-fault experiments, which will be added to this file.

Command:
```bash
set -o pipefail && python -m pytest -q tests/test_leakage.py::test_cnt_roll_3_uses_only_previous_days 2>&1 | tee /tmp/bikeshare-cnt-roll-3-red.txt
```

Actual output:
```text
F                                                                        [100%]
=================================== FAILURES ===================================
___________________ test_cnt_roll_3_uses_only_previous_days ____________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_cnt_roll_3_uses_only_previous_days(feats):
>       assert "cnt_roll_3" in feats.columns, "cnt_roll_3 has not been implemented"
E       AssertionError: cnt_roll_3 has not been implemented
E       assert 'cnt_roll_3' in Index(['dteday', 'instant', 'season', 'yr', 'mnth', 'holiday', 'weekday',\n       'temp', 'atemp', 'hum', 'windspeed', ...kday', 'month_sin', 'month_cos',\n       'weather_severity', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7'],\n      dtype='str')
E        +  where Index(['dteday', 'instant', 'season', 'yr', 'mnth', 'holiday', 'weekday',\n       'temp', 'atemp', 'hum', 'windspeed', ...kday', 'month_sin', 'month_cos',\n       'weather_severity', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7'],\n      dtype='str') =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7\n0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857\n713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571\n\n[714 rows x 28 columns].columns

tests/test_leakage.py:70: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_roll_3_uses_only_previous_days - Asser...
1 failed in 0.66s
```

The test fails because cnt_roll_3 is missing, before feature implementation.

## forbidden: let "casual" through while FORBIDDEN unchanged

**Argument:** `forbidden`  
**Starting commit:** `1cf15ddfb891393e730b652c97698ad2ddada6df`  

### Commands executed
```bash
git --no-pager diff --exit-code HEAD -- src/features.py  # clean-state check
git rev-parse HEAD                                        # 1cf15ddfb891393e730b652c97698ad2ddada6df
git show HEAD:src/features.py > /tmp/bikeshare-forbidden-original.py   # save original
# Edit tool: introduced the fault
git --no-pager diff HEAD -- src/features.py > /tmp/bikeshare-forbidden.diff    # save diff
python -m pytest tests/test_leakage.py::test_no_forbidden_features -q 2>&1 | tee /tmp/bikeshare-forbidden-pytest-fail.txt   # capture failure
# Edit tool: restored the original code
python -m pytest tests/test_leakage.py -q                  # passing pytest
git --no-pager diff HEAD -- src/features.py                # restoration check (empty)
```

**Note:** The failing-test pipeline did not enable pipefail. The log demonstrates the assertion failure, but the pipeline's shell exit status does not establish pytest's exit status.

### Hook stderr
Transcribed from the automatic PostToolUse error displayed in the session; formatting is not preserved byte-for-byte.
```text
Leakage tests failed after editing /Users/evelynzhang/Downloads/bikeshare-open/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info =============
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 8 passed in 0.84s
```

### Git diff (verbatim from /tmp/bikeshare-forbidden.diff)
```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..5b77487 100644
--- a/src/features.py
+++ b/src/features.py
@@ -82,7 +82,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
 def feature_columns(df: pd.DataFrame) -> list[str]:
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN or c == "casual"]
 
 
 if __name__ == "__main__":
```

### Failing pytest output (verbatim from /tmp/bikeshare-forbidden-pytest-fail.txt)
```text
F                                                                        [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed in 0.70s
```

### Repair note
One corrective Edit (reverting the `or c == "casual"` line) restored the original code. The PostToolUse hook error above is the same as what was displayed when the fault was injected. No additional edits were needed.

**Passing test output:** After repair, `python -m pytest tests/test_leakage.py -q` showed `9 passed in 0.60s`.

## rolling: include today's count in cnt_roll_7

**Argument:** `rolling`

**Starting commit:** `7518747096a9d3e3f25225e35438b11fd8c7517a`

**Runtime observed:** Claude Code 2.1.327; model alias `bikeshare-coder`.

**Fault:** Removing only `.shift(1)` from `cnt_roll_7` made its window include the current day's count and the previous six calendar days, rather than the seven days strictly before prediction. Other features, including `cnt_roll_3`, were preserved.

**Repair count:** One corrective Edit restored `.shift(1)`. This counts corrective edits after the hook detected the fault, not setup discussion or tool calls. The user approved the restoration edit.

### Passing baseline — saved output

```text
.........                                                                [100%]
9 passed in 0.94s
```

### Fault capture and restoration commands

```bash
# Save the fault diff after the Edit tool introduced it.
git --no-pager diff HEAD -- src/features.py > /tmp/bikeshare-rolling.diff && echo "Diff saved to /tmp/bikeshare-rolling.diff"

# Capture the failing tests before the corrective Edit.
set -o pipefail
python -m pytest -q tests/test_leakage.py 2>&1 | tee /tmp/bikeshare-rolling-fail.txt; echo "Exit code: ${PIPESTATUS[0]}"

# The Edit tool then restored .shift(1); capture passing tests.
set -o pipefail
python -m pytest -q tests/test_leakage.py 2>&1 | tee /tmp/bikeshare-rolling-pass.txt; echo "Exit code: ${PIPESTATUS[0]}"

# Check restoration.
cmp src/features.py /tmp/bikeshare-rolling-original.py && echo "✓ File byte-identical to original" || echo "✗ Files differ"
git --no-pager diff --exit-code HEAD -- src/features.py; echo "Exit code: ${PIPESTATUS[0]}"
```

The failing and passing test commands enabled `pipefail`, but their trailing `echo` commands did not preserve pytest's status as the final shell status. The visible `Exit code:` lines were blank; no numeric exit status is claimed from them. The pytest logs establish the test outcomes. The baseline's printed success banner alone was not used as evidence.

### Automatic PostToolUse hook — original terminal transcript

The following block is copied unchanged from the terminal transcript supplied on 2026-11-18. It retains Claude Code's UI prefix, indentation, and line wrapping; it is not a separately captured raw stderr file. The hook ran automatically after the fault Edit, not through a manual hook invocation.

```text
  ⎿  PostToolUse:Edit hook reported a problem
     [${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed
     after editing /Users/evelynzhang/Downloads/bikeshare-open/src/features.py:
     [714 rows x 29 columns]

         def test_rolling_mean_excludes_today(feats):
             """cnt_roll_7 must be the mean of the 7 calendar days *before*
     today."""
             by_date = feats.set_index("dteday")[TARGET]
             date = feats.dteday.iloc[200]
             window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
             if all(d in by_date.index for d in window):
                 expected = sum(by_date[d] for d in window) / 7
     >           assert feats.set_index("dteday").cnt_roll_7[date] ==
     pytest.approx(expected)
     E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
     E
     E             comparison failed
     E             Obtained: 4389.0
     E             Expected: 4414.857142857143 ± 0.00441486

     tests/test_leakage.py:57: AssertionError
     ============================ short test summary info
     ============================
     FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert
     np.flo...
     1 failed, 8 passed in 0.73s
```

### Actual fault diff — copied from /tmp/bikeshare-rolling.diff

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..97a81f4 100644
--- a/src/features.py
+++ b/src/features.py
@@ -73,7 +73,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
     # If you add a longer lag, raise LAG_WARMUP in src/config.py.
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
     out["cnt_roll_3"] = out[TARGET].shift(1).rolling(3).mean()
 
     return out.dropna().reset_index(drop=True)
```

### Failing tests — copied from /tmp/bikeshare-rolling-fail.txt

```text
....F....                                                                [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....428571  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143  2077.333333

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 8 passed in 0.75s
```

### Passing tests after repair — copied from /tmp/bikeshare-rolling-pass.txt

```text
.........                                                                [100%]
9 passed in 0.46s
```

### Restoration

The session's `cmp` check printed `✓ File byte-identical to original`; the Git comparison displayed no diff. Before appending this record, the recording script also compared `src/features.py` byte-for-byte with both `/tmp/bikeshare-rolling-original.py` and the source at the recorded starting commit. The recording script did not rerun tests.

## weather: suppress the unknown-label exception

**Argument:** `weather`

**Starting commit:** `6675e4d7936adaf0270c3089b8c183e9bb1abbaa`

**Claude session:** `b6bead52-ba07-4789-b3c2-68230dd6f0e0`

**Evidence recording:** A ChatGPT-generated Python recorder copied the existing logs and original saved hook message; it did not rerun the experiment.

**Fault:** The Edit tool replaced only the unknown-label `raise ValueError(...)` in `encode_weather()` with `pass`. The test supplied `UNEXPECTED`, but the function returned without the required exception. Raw data and tests were not changed for this experiment.

**Repair count:** The session reported one corrective Edit to restore the original raise statement. This counts repair edits after fault injection, not preliminary discussion or shell calls. The restored source was independently compared byte-for-byte with the backup and the recorded Git commit before this record was appended.

### Passing baseline — original saved output

```text
.........                                                                [100%]
9 passed in 1.05s
```

### Recorded Bash commands

The following command text is copied directly from the session's relevant Bash tool calls, in recorded order. Repeated serialized copies of the same tool-call ID are included only once. These commands were not rerun while preparing this record.

Command 1:

```bash
git --no-pager diff --exit-code HEAD -- src/features.py
```

Command 2:

```bash
git rev-parse HEAD > /tmp/bikeshare-weather-start.txt && git show HEAD:src/features.py > /tmp/bikeshare-weather-original.py && echo "Starting state saved:" && cat /tmp/bikeshare-weather-start.txt
```

Command 3:

```bash
set -o pipefail && python -m pytest -q tests/test_leakage.py 2>&1 | tee /tmp/bikeshare-weather-baseline.txt
```

Command 4:

```bash
git --no-pager diff HEAD -- src/features.py > /tmp/bikeshare-weather.diff && echo "Diff saved to /tmp/bikeshare-weather.diff:" && cat /tmp/bikeshare-weather.diff
```

Command 5:

```bash
set -o pipefail && python -m pytest -q tests/test_leakage.py 2>&1 | tee /tmp/bikeshare-weather-fail.txt
```

Command 6:

```bash
set -o pipefail && python -m pytest -q tests/test_leakage.py 2>&1 | tee /tmp/bikeshare-weather-pass.txt
```

Command 7:

```bash
cmp src/features.py /tmp/bikeshare-weather-original.py && echo "✓ Files match: src/features.py equals original" || echo "✗ Files differ"
```

Command 8:

```bash
git --no-pager diff --exit-code HEAD -- src/features.py && echo "✓ Git diff is clean - file restored successfully" || echo "✗ File has changes from HEAD"
```

### Automatic PostToolUse hook — original saved message

Recovered from the saved Claude session. It appeared in 3 nested/wrapped representations of the same failure message; these are not counted as separate fault experiments. The innermost recorded message is copied unchanged below, including its hook-command prefix, and saved to `/tmp/bikeshare-weather-hook.txt`. This was the automatic Edit hook, not a manually invoked hook or the separate pytest capture.

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/evelynzhang/Downloads/bikeshare-open/src/features.py:
........F                                                                 [100%]
=================================== FAILURES ====================================
_______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        labels = pd.Series(["GOOD", "MISTY", "BAD", "UNEXPECTED"])
>       with pytest.raises(ValueError, match="unmapped weather labels"):
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:80: Failed
============================ short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID ...
1 failed, 8 passed in 0.71s
```

### Actual fault diff — /tmp/bikeshare-weather.diff

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..63a2660 100644
--- a/src/features.py
+++ b/src/features.py
@@ -27,7 +27,7 @@ def encode_weather(series: pd.Series) -> pd.Series:
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
     if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
+        pass
     return series.map(WEATHER_ORDER).astype(float)
 
 
```

### Failing tests — /tmp/bikeshare-weather-fail.txt

```text
........F                                                                [100%]
=================================== FAILURES ===================================
______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        labels = pd.Series(["GOOD", "MISTY", "BAD", "UNEXPECTED"])
>       with pytest.raises(ValueError, match="unmapped weather labels"):
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:80: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID...
1 failed, 8 passed in 0.52s
```

### Passing tests after repair — /tmp/bikeshare-weather-pass.txt

```text
.........                                                                [100%]
9 passed in 0.46s
```

### Restoration

The separate Terminal check printed `Source restored byte-for-byte: True`. The recorder also checked the current source against both `/tmp/bikeshare-weather-original.py` and `src/features.py` at the starting commit. No tests or forecasting models were run by the recorder. Numeric shell exit statuses are not inferred from the model's summary; the original test results are preserved above.


## Fourth experiment: Bash copy blocked before execution

Starting commit: `e93c227141d37107a7fbb19d6a665cd8e1d196b0`

### Attempted Bash command

```bash
cp /tmp/bikeshare-raw-copy/faulty.csv data/raw/bike_daily.csv
```

### Observed permission denial

The following message is transcribed from the actual tool result supplied in the conversation. It is not hook stderr or a new execution log.

```text
Error: Permission to use Bash with command cp
/tmp/bikeshare-raw-copy/faulty.csv data/raw/bike_daily.csv has been denied.
```

The copy was denied before execution. The recorded raw-file observation matched the original, and the verification required zero restoration writes and zero corrective Edit tool calls. No automatic PostToolUse hook failure was displayed for this attempted copy. The helper's exit code 1 reported that the candidate was absent, while its verification pytest run exited 0.

This is a blocked attempt, not a successful fault injection. It does not demonstrate whether the PostToolUse hook would detect an actual raw-data modification, and there is no failing pytest output for this attempt.

### Permission context

The displayed session was in Plan mode. Its Deny tab listed `Bash(rm -rf:*)`, `Edit(./data/raw/**)`, and `Write(./data/raw/**)`. The denial message did not identify the exact check responsible. The Edit rule is a plausible explanation: current [Claude Code documentation](https://code.claude.com/docs/en/permissions#what-read-and-edit-rules-cover) says file deny rules also apply to recognized Bash file commands. This explanation is an inference, not a diagnostic from the tool.

### Baseline command

Copied from `/private/tmp/bikeshare-raw-copy/baseline-command.txt` without changing its contents.

```text
/Users/evelynzhang/Downloads/bikeshare-open/.venv/bin/python -m pytest -q --color=no tests/test_leakage.py
```

### Baseline output

Copied from `/private/tmp/bikeshare-raw-copy/baseline.txt` without changing its contents.

```text
.........                                                                [100%]
9 passed in 1.01s
```

### Baseline exit status

Copied from `/private/tmp/bikeshare-raw-copy/baseline-status.json` without changing its contents.

```text
{
  "exit_code": 0
}
```

### Raw-file observation

Copied from `/private/tmp/bikeshare-raw-copy/observed-raw.json` without changing its contents.

```text
{
  "sha256": "a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc",
  "matches_original": true,
  "matches_candidate": false
}
```

### Verification command

Copied from `/private/tmp/bikeshare-raw-copy/pass-command.txt` without changing its contents.

```text
/Users/evelynzhang/Downloads/bikeshare-open/.venv/bin/python -m pytest -q --color=no tests/test_leakage.py
```

### Verification output

Copied from `/private/tmp/bikeshare-raw-copy/pass.txt` without changing its contents.

```text
.........                                                                [100%]
9 passed in 1.11s
```

### Verification exit status

Copied from `/private/tmp/bikeshare-raw-copy/pass-status.json` without changing its contents.

```text
{
  "exit_code": 0
}
```

### Recorded result

Copied from `/private/tmp/bikeshare-raw-copy/result.json` without changing its contents.

```text
{
  "expected_manual_failure_observed": false,
  "restoration_writes": 0,
  "corrective_Edit_tool_calls": 0,
  "issues": [
    "Expected candidate is not present; do not claim the Bash fault succeeded"
  ],
  "hook_observation": "Must be taken from the separate Claude Bash tool result, not this helper"
}
```

### Restoration verification

Copied from `/private/tmp/bikeshare-raw-copy/restoration.json` without changing its contents.

```text
{
  "byte_for_byte_match": true,
  "sha256": "a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc",
  "write_performed": false
}
```

### Additional protection

A SHA-256 comparison against the trusted original CSV during ingestion or make data would detect an unexpected raw-data modification before the pipeline proceeds. A Stop hook performing that comparison could also detect a modification before the agent finishes. Neither additional control was implemented in this experiment.

### Attribution

The experiment helper and this evidence-recording script were drafted with ChatGPT assistance. Test output and JSON records above were read from the saved execution evidence; the permission denial was transcribed from the displayed tool result. The recorder did not rerun tests or models.


## Later protection: ingestion hash guard (2026-11-24)

The blocked Bash attempt above remains a blocked attempt. No raw-data fault
was injected again. In freeze commit `af4e0962caddcb0bd8a824a1df5eaa33ee8935df`,
`load_raw()` gained a SHA-256 comparison against the original committed CSV,
before parsing. `make data` and the data stage of `make all` now reject altered
bytes even if the change occurred outside the Edit/Write PostToolUse hook.
This is detection at ingestion, not a claim that the hook sees Bash copies.

The [actual Git diff](evidence/raw-integrity-guard.diff) was captured with:

```bash
git diff c629cd1fa165b25c7733df5921d3d08476c957aa af4e0962caddcb0bd8a824a1df5eaa33ee8935df -- src/config.py src/ingest.py tests/test_contract.py
```

That diff includes the other frozen changes to these files as well.
`test_ingest_rejects_modified_raw_copy` adds a newline to a temporary copy,
redirects ingestion to that copy, and expects the hash-mismatch ValueError.
The repository's raw CSV is never edited by this test. It passed as part of
the actual [24-test run](evidence/final-prefreeze-tests.log), run with
`make test` under the pinned environment. The final pipeline and artifact
verification also confirm the original raw SHA-256 is unchanged. This does
not supply missing execution or hook evidence for the earlier denied copy.
