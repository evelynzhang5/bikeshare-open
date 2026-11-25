# Submission requirement check

Reviewed on 2026-11-25 against the [official assignment](https://dsc-capstone.org/2026-27/assignments/methodology/07-open/).
The starting main commit was `87c0130366ff3316f401aeab9c145b6bd58fdb2f`.
This change adds a leakage test and its evidence; it leaves the frozen pipeline,
raw data, scores, predictions, and original audit output intact.

## Requirement mapping

| Rubric item | Evidence checked | Status and qualification |
| --- | --- | --- |
| Reproducible repository (15) | Pinned requirements; actual earlier clean `make all` log; unchanged pipeline/artifact hashes; 32 report values equal committed metrics; reports tracked and generated files ignored | Evidence present. `make all` was not rerun during this review. The earlier prediction verification recomputed saved scores without refitting. |
| CLAUDE.md (10) | Exclusions, temporal split, both baselines, pipeline commands, feature rules, own skill, and renamed-count rule | 53 lines, under 60. |
| Verification suite (25) | Original tests; named-date `cnt_roll_3` test committed before implementation; raw-column classification; three original fault records; new value-based leak guard | Clean suite: 28 passed. The old suite missed a renamed target; the added guard rejects it and the other recorded affine probes. Fourth-fault evidence remains qualified below. |
| Results with baselines (20) | Exactly five required report sections; eight before/after table rows; negative HGB finding; feature validation delta; Exercise 4 transformation; Exercise 5 persistence comparison | Present. The selected configuration was frozen before final H2 scoring. No subsequent selection changed. |
| Structural enforcement (10) | Original hook script, hook wiring and permission denials preserved; three automatic hook error records; actual later ingestion hash-guard diff and passing temporary-copy test | Present with evidence limitations: the fourth copy was denied before execution; the forbidden-column hook text is labeled as a transcription. |
| Agent configuration (10) | Own `seed-fault` skill takes `$ARGUMENTS`; starter `new-feature` skill retained; complete peer output plus separate verdict; own successful SDK JSON | Present. Own SDK output is pinned to the actual run at `08f33aa`; no new LLM audit was run for this test/documentation change. |
| Decisions and attribution (10) | Original five decision entries; dated additions; model/size/context/switch; agent-generated and methodological-decision lists; chronological commits | Present. The student still needs to review and adopt the stated judgments. |

These statuses are evidence checks, not awarded points or a guarantee of a grade.
The Markdown report has the required structure; rendered page length depends on
the reader/export settings and should be checked against the requested 2–4 pages.

## Actual checks and limits

The [machine-readable check](evidence/submission-check.json) records 24 passing
file/history/evidence checks. The first commit exactly matches the downloaded
starter ZIP, every starter file remains, the raw CSV matches the original
SHA-256, and all final-run source/artifact hashes still match their recorded
values. The peer capture's hash and its verbatim block also match.

The new guard checks actual input values rather than only column names. It
searches affine combinations of up to three inputs for reconstruction of
unavailable same-day `cnt`, `casual`, or `registered`. It does not certify
arbitrary nonlinear/noisy leaks or combinations requiring more inputs.
The [additional fault evidence](SEEDED_FAULTS.md#additional-rubric-check-renamed-same-day-counts-2026-11-25)
contains actual commands, diffs, complete outputs, and numeric return codes.
These extra probes were disposable-copy checks, not automatic Claude hook runs.

The final pipeline's original run and frozen results were preserved. The test
suite retains its H1-only quality fit, but this review performed no H2 model
fit, generated no new forecasting predictions, and changed no selected model.
The successful SDK audit remains its original captured result, not a new claim
about every possible failure of the verification suite.

## Items that cannot be marked unconditionally complete

1. **Fourth seeded fault:** the attempted Bash copy was denied before execution.
   Its failure output, unchanged raw hash, zero repairs, and passing verification
   are recorded honestly. A later SHA-256 guard is implemented and tested, but it
   does not turn the blocked attempt into a successful fault injection. The
   rubric asks for real output for all four faults. Ask course staff whether the
   blocked attempt plus implemented protection satisfies that requirement; if
   they require an actual demonstration, perform it through the prescribed local
   workflow and preserve real evidence. Do not remove or bypass permission rules
   merely to make the transcript look complete.
2. **Historical evidence precision:** the forbidden-column hook message is a
   transcript with formatting differences, and its failing pipeline did not use
   `pipefail`. The actual assertion failure is recorded, but a numeric pytest
   exit code is not inferred from that pipeline. The rolling record separately
   discloses its blank status output. These limits remain explicit.
3. **Submission and ownership:** review the report's judgments and rendered
   length, then submit the GitHub repository URL through the course form. This
   review did not submit the assignment or verify a course submission receipt.

Prepared with ChatGPT/Codex assistance. New test evidence was generated by the
commands recorded in the logs/manifest; historical Claude output was not rewritten.
