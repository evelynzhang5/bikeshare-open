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
