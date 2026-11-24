# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

[2026-11-17] Switched from nvfp4 variant after observing high memory use. Configured Ollama settings: one loaded model, one parallel request, Flash Attention enabled, and q8_0 KV cache.

[2026-11-17] Added cnt_roll_3 (three-day historical demand average): uses only the three previous calendar days (d-1, d-2, d-3), all known at prediction time for date d; test suite confirms strict temporality and row counts are 714 rows with 15 features.

[2026-11-17] Added an explicit raw-column classification check so newly introduced columns require review before use.

[2026-11-17] Added an unknown-weather regression test so removing the encoder's explicit error check will produce a failing test.

[2026-11-18] Added seed-fault, drafted with ChatGPT assistance, to standardize fault injection, evidence capture, and restoration; documented its usage in CLAUDE.md.

[2026-11-23] `cnt_roll_3` uses counts from the three previous calendar days, available for a one-day prediction. The recorded H1 comparison changed Ridge R2 by -0.0036385 and MAE by +3.5490, and HGB R2 by -0.0202049 and MAE by +14.9810. Use the original 14 inputs for Exercise 4; recommend dropping the candidate from the selected model, while retaining its implementation and test-first evidence. The default feature builder remains unchanged.

[2026-11-23] Exercise 4 (ChatGPT/Codex-assisted): train HGB on `cnt - cnt_lag_1` and add the known lag back before scoring. H1 R2 improved from 0.2185 to 0.6079 and MAE from 1296.6 to 834.3; Ridge remained better at R2 0.6475 and MAE 832.9. This is a defensible persistence-plus-correction model for sequential one-day prediction, conditional on the existing observed-weather inputs; it does not establish operational day-ahead performance. Tried one specified transformation with unchanged hyperparameters and no H2 scoring; preserve the untransformed pipeline for final metrics.

[2026-11-23] Added validation-only target experimentation, reconstruction, and held-out evaluation rules to CLAUDE.md. The file remains under 60 lines. Original source/data hashes, actual metrics, prediction rows, and verification logs are recorded in docs/EXERCISE4_VALIDATION.md and docs/evidence/.

[2026-11-24] Freeze before final H2 scoring: select untransformed Ridge with the original 14 inputs. Drop `cnt_roll_3` from the selected configuration because its H1 R2 and MAE both worsened; retain its implementation and report both feature sets as the required fixed ablation. Do not change hyperparameters or choose a model after viewing H2 scores. Exercise 4 remains validation-only; the transformed tree still trailed Ridge there.

[2026-11-24] Preserve the model-quality assertion but move its evaluation from H2 to H1, preventing repeated held-out scoring during ordinary tests. Clone estimators for independent fits. Extend the final pipeline to emit the required eight untransformed metric rows and saved predictions; track reports/ by removing its ignore rules.

[2026-11-24] Enforce the original raw CSV SHA-256 during ingestion, including writes outside the Edit/Write hook. A synthetic temporary-copy test verifies rejection without modifying the repository's raw file. This adds protection but does not turn the earlier blocked Bash-copy attempt into a successful fault injection.

[2026-11-24] Repair the SDK auditor's CSV-only reader to accept the actual processed Parquet table, distinguish legitimate historical lags from same-day leakage, read project/local endpoint settings explicitly, restrict built-in tools, and reject malformed/error reports. Deterministic tests cover the tool and report validation; a real local-model audit is still required. Updated CLAUDE.md accordingly, including removal of the overly broad claim about boosted trees' target-range limits.
