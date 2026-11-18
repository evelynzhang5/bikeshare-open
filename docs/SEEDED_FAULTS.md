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
