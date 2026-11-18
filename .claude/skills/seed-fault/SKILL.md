---
name: seed-fault
description: Demonstrate one feature fault, capture real failure evidence, restore the code, and document the result.
disable-model-invocation: true
---

# Fault experiment: $ARGUMENTS

Accept one argument: forbidden, rolling, or weather.
Perform exactly one experiment per invocation.

1. Check git status. Require src/features.py and tests/ to have no
   uncommitted changes. Record the starting commit.
2. Run `python -m pytest tests/test_leakage.py -q`.
   Continue only when the baseline passes.
3. Use the Edit tool to introduce exactly one temporary fault in
   src/features.py:
   - forbidden: let "casual" through feature_columns while leaving
     FORBIDDEN unchanged.
   - rolling: remove only .shift(1) from cnt_roll_7.
   - weather: replace the unknown-label raise statement with pass,
     retaining valid Python syntax.
4. Observe the automatic PostToolUse hook. Preserve its actual stderr.
   Never substitute an invented message or a manual hook invocation.
5. Before repairing, save the exact git diff and capture a real pytest
   run to a temporary log using tee with pipefail enabled.
6. Reverse only the injected change using Edit. Preserve all tests.
   Run the leakage tests again and verify that src/features.py matches
   its starting version.
7. Append to docs/SEEDED_FAULTS.md: the argument, starting commit,
   exact diff, verbatim failing pytest output, actual hook stderr,
   observed repair-turn count, and actual passing test output.
   Preserve existing evidence. If hook evidence was unavailable,
   report that explicitly after restoring the code; do not claim
   the experiment is complete.
8. Show the resulting documentation diff and stop without committing.

Do not modify raw data, tests, split rules, or forecasting models.
Do not train or score models. Do not run make test, make train, or make all.
Do not disable hooks or fabricate output.
