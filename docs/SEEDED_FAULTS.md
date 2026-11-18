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
