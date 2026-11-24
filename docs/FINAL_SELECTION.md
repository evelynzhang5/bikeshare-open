# Final evaluation protocol, frozen before H2 scoring

Base: `c629cd1fa165b25c7733df5921d3d08476c957aa`.

The selected model is untransformed Ridge (alpha=1.0, train-fitted
StandardScaler) on the original 14 inputs. The new `cnt_roll_3` stays implemented
and tested but is excluded from this selected feature set. Its H1 validation
R2 and MAE both worsened. HGB retains random_state=0 and max_iter=300; both
mean and persistence baselines are retained. No hyperparameters change.

Final evaluation will fit all four methods on 2011 and score the predetermined
14-input and 15-input variants on H1 and H2 2012. The eight-row comparison is
required evidence, not a new search over test performance. The selected model
will not change after these scores are observed. Exercise 4's daily-change
transformation remains a validation-only experiment.

The pipeline will save rounded metrics and the predictions used to calculate
them. Ordinary tests now measure model quality on H1. After final evaluation,
verification may recalculate metrics from the saved predictions without refitting
models. The local SDK auditor will inspect this evidence and structural tests.

Earlier starter documentation and the peer audit exposed example H2 scores;
this protocol does not claim those numbers were unknown. Own feature and target
comparisons used only H1; the final code choices are fixed here before this
project's final held-out scoring run.

This protocol and implementation were prepared with ChatGPT/Codex assistance.
