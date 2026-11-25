# Repairing the local SDK audit's output limit

The [official assignment](https://dsc-capstone.org/2026-27/assignments/methodology/07-open/)
requires a real `python agent/audit.py . --out reports/audit.jsonl` run on the
finished repository. A failed run is not a clean methodology verdict.

## Observed failure

The user ran `make audit` at commit `28052b4b622e24d5b91355825c8b67bfaeb68eed`.
Feature construction succeeded. The following is copied from the failure JSON
the user supplied in the conversation, not from a new execution in this workspace:

```json
{"repo": "", "error": "run_failed", "raw": "Claude Code returned an error result: API Error: Claude's response exceeded the 32000 output token maximum. To configure this behavior, set the CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable. (exit code: 1)", "audited_commit": "28052b4b622e24d5b91355825c8b67bfaeb68eed"}
```

The recorded cause is output-token exhaustion. The `unrecognized_model` warning
also appeared in the earlier successful peer audit and in the request-capture
test below; it does not by itself establish an endpoint failure. The old summary
counted only leakage findings, making a failed attempt misleadingly read as
`0 flagged`. That summary is corrected to show completed and failed counts.

## Changes and scope

- Keep `bikeshare-coder`, the 65,536-token context, the SDK, and schema validation.
  Bound each response to 4,096 tokens and request concise intermediate output.
- Set the native thinking control off and include
  `{"thinking":{"type":"disabled"}}` through `CLAUDE_CODE_EXTRA_BODY` for this
  audit process. The native control alone omitted the field for this custom model
  in our request probe; an omitted field can leave Ollama's model default active.
- Use only the configured audit MCP server, display tool names as progress,
  retain SDK error details, and resolve the repository path before error reporting.
- Save a previous failure log under a unique name before replacing the latest
  `.failed.jsonl`. A failed retry cannot overwrite a successful `audit.jsonl`.

`CLAUDE_CODE_EXTRA_BODY` was verified against the CLI bundled with the pinned
SDK. It is an implementation-dependent compatibility mechanism, not a promise
about every future CLI release. The regression test checks the actual request,
rather than only asserting that a Python option was set. Ollama documents
[`thinking.type: disabled`](https://docs.ollama.com/api/anthropic-compatibility)
as an explicit off switch for compatible models.

## Actual verification

Environment: `claude-agent-sdk==0.2.172`, bundled Claude Code `2.1.308`, Python
3.12.14. Command:

```bash
set -o pipefail
python -m pytest -q -s tests/test_auditor.py 2>&1 | tee docs/evidence/sdk-audit-controls-tests.log
```

The [saved output](evidence/sdk-audit-controls-tests.log) records six passing
checks, including a loopback HTTP request showing `max_tokens: 4096` and
`thinking: {type: disabled}`. That test endpoint deliberately returns HTTP 400;
it inspects the SDK's transport and **does not call an LLM or perform an audit**.
The tests also cover CSV/Parquet identity checks, report validation, and failure
log preservation. No forecasting models were fitted or scored.

## Completed local rerun

The user pulled the repair and reran `make audit` on the Mac at commit
`08f33aaf3826e65e2926e6a2dc361ddbd8be1edb`. The supplied terminal summary was:

```text
attempted 1; completed 1; failed 0; flagged among completed 0 -> reports/audit.jsonl
```

The user then supplied the result of `cat reports/audit.jsonl` and
`git status --short`. The exact JSON line is preserved in
[reports/audit.jsonl](../reports/audit.jsonl). It reports no leakage,
all three boolean checks true, an empty findings list, and high confidence.
The reported status was:

```text
?? reports/audit.failed.jsonl
?? reports/audit.jsonl
```

Thus the reported status showed no tracked-file changes after the run.
The original failed attempt remains separately documented above. The successful
output is evidence from the user's actual local run, copied from the supplied
terminal contents, not a result generated or inferred in this cloud workspace.
`REPORT.md` records the verdict without using it to dismiss the benchmark's
weather-availability limitation or the blocked fourth experiment.

This repair and its tests were prepared with ChatGPT/Codex assistance.
