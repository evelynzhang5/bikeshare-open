"""Batch leakage auditor built on the Claude Agent SDK.

Why this exists: the `/leakage-auditor` subagent inside Claude Code is the
right tool for reviewing *your* diff, once, while you watch. This script is
the right tool for reviewing *forty* repos, unattended, and getting back a
row per repo you can put in a dataframe. Same reviewer, different harness.

    pip install claude-agent-sdk
    python agent/audit.py ../student-repos/*/ --out audit.jsonl

The SDK drives the same Claude Code binary the tutorial uses, so it reads
the same endpoint settings: with Ollama running locally and
.claude/settings.json pointing at it, no API key is needed. The model
comes from AUDIT_MODEL (default: the local `bikeshare-coder` build).
To run against a hosted model instead, set ANTHROPIC_BASE_URL /
ANTHROPIC_AUTH_TOKEN and AUDIT_MODEL in the environment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    create_sdk_mcp_server,
    query,
    tool,
)

# --------------------------------------------------------------------------
# A custom tool. The model is bad at deciding whether three float columns
# sum to a fourth; numpy is perfect at it. Give the deterministic part to
# code and leave the judgement to the model.
# --------------------------------------------------------------------------


@tool(
    "check_identity",
    "Test whether any subset of candidate columns is an exact linear "
    "restatement of the target column. Returns the offending subsets.",
    {"csv_path": str, "target": str, "candidates": list},
)
async def check_identity(args: dict[str, Any]) -> dict[str, Any]:
    path = Path(args["csv_path"])
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    cols = [c for c in args["candidates"] if c in df.columns and c != args["target"]]

    # Least squares with an intercept column, so `cnt = a*x + b` is caught
    # as well as `cnt = casual + registered`. Rows with any NaN are dropped
    # first; lstsq on NaN returns garbage rather than raising.
    hits = []
    for r in (1, 2, 3):
        for subset in _combinations(cols, r):
            block = df[list(subset) + [args["target"]]].dropna()
            if len(block) < r + 2:
                continue
            X = np.column_stack([block[list(subset)].to_numpy(dtype=float),
                                 np.ones(len(block))])
            y = block[args["target"]].to_numpy(dtype=float)
            coef, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid = float(np.abs(X @ coef - y).max())
            if resid < 1e-6:
                hits.append({"columns": list(subset), "max_residual": resid})
    verdict = "LEAKAGE" if hits else "clean"
    return {
        "content": [
            {"type": "text", "text": json.dumps({"verdict": verdict, "identities": hits})}
        ]
    }


def _combinations(items, r):
    from itertools import combinations

    return combinations(items, r)


auditor_tools = create_sdk_mcp_server(
    name="audit", version="1.0.0", tools=[check_identity]
)

SYSTEM = """\
You review student data-science repos for methodology errors. You did not
write this code and you have no stake in it passing.

Check exactly four things:
  1. Target leakage: same-day or future target information in actual model
     inputs. Strictly historical target lags are legitimate. Obtain each
     input list from reports/metrics.json and pass only those candidates
     to check_identity on data/processed/features.parquet (the tool's
     csv_path argument accepts Parquet too). Excluded raw identity columns
     are not evidence that the fitted models use them.
  2. Temporal validity: splits by date not at random; every rolling or
     lag feature shifts before it aggregates; no transformer is fit on
     validation or test rows.
  3. Baseline: both mean and naive-persistence baselines reported next to
     every model score.
  4. Reproducibility: the pipeline runs from a documented command and
     random seeds are fixed.

Verify by reading files and running structural tests or recalculating scores
from reports/predictions.csv. Read docs/evidence/final-pipeline.log for the
recorded pipeline run. Do not refit models, change files, or run make all or
make train during this audit. Do not launch other agents. Do not accept a
docstring or README claim as evidence. Explain coverage limits in findings.
Evaluate the stated limitation that realized same-day weather is not known
for operational day-ahead prediction, rather than omitting it from the audit.

Your final answer is a single JSON object matching the schema you were
given. No prose around it.
"""

# Enforced by the SDK: the final turn must validate against this schema and
# arrives parsed in ResultMessage.structured_output. Asking nicely in the
# prompt is not a contract; a schema is.
REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "repo": {"type": "string"},
        "leakage": {"type": "string", "enum": ["none", "suspected", "confirmed"]},
        "temporal_ok": {"type": "boolean"},
        "baseline_reported": {"type": "boolean"},
        "reproducible": {"type": "boolean"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "issue": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                },
                "required": ["file", "line", "issue", "why_it_matters"],
            },
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["repo", "leakage", "temporal_ok", "baseline_reported",
                 "reproducible", "findings", "confidence"],
}


async def audit_repo(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    print(f"Auditing {repo.name} with {os.environ.get('AUDIT_MODEL', 'bikeshare-coder')}",
          file=sys.stderr, flush=True)
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM,
        cwd=str(repo),
        setting_sources=["project", "local"],
        tools=["Read", "Grep", "Glob", "Bash"],
        disallowed_tools=["Edit", "Write", "NotebookEdit"],
        mcp_servers={"audit": auditor_tools},
        allowed_tools=[
            "Read",
            "Grep",
            "Glob",
            "Bash",
            "mcp__audit__check_identity",
        ],
        # tools limits built-ins; allowed_tools controls permission grants.
        # Bash still has shell capabilities: this is not a filesystem sandbox.
        permission_mode="default",
        max_turns=40,
        model=os.environ.get("AUDIT_MODEL", "bikeshare-coder"),
        output_format={"type": "json_schema", "schema": REPORT_SCHEMA},
        stderr=lambda line: print(line, file=sys.stderr, flush=True),
    )

    # Only the ResultMessage carries the final answer. Concatenating every
    # intermediate TextBlock ("Let me look at config.py first...") and
    # json.loads-ing the lot fails on the first repo that thinks out loud.
    final: ResultMessage | None = None
    async for message in query(prompt=f"Audit the repo at {repo}.", options=options):
        if isinstance(message, ResultMessage):
            final = message

    if final is None or final.is_error:
        return {"repo": repo.name, "error": "run_failed",
                "raw": (final.result or "")[:500] if final else ""}
    if final.structured_output is not None:
        data = final.structured_output
    else:
        try:
            data = json.loads((final.result or "").strip())
        except json.JSONDecodeError:
            return {"repo": repo.name, "error": "unparseable", "raw": (final.result or "")[:500]}
    try:
        validate_report(data)
    except ValueError as exc:
        return {"repo": repo.name, "error": "invalid_report", "raw": str(exc)}
    return {**data, "repo": repo.name}


def validate_report(data: Any) -> None:
    """Check fallback text as strictly as the schema's required fields."""
    if not isinstance(data, dict) or not set(REPORT_SCHEMA["required"]) <= data.keys():
        raise ValueError("Missing required report fields")
    if not isinstance(data["repo"], str):
        raise ValueError("repo must be a string")
    for field in ("temporal_ok", "baseline_reported", "reproducible"):
        if type(data[field]) is not bool:
            raise ValueError(f"{field} must be boolean")
    if data["leakage"] not in ("none", "suspected", "confirmed"):
        raise ValueError("Invalid leakage verdict")
    if data["confidence"] not in ("low", "medium", "high"):
        raise ValueError("Invalid confidence")
    if not isinstance(data["findings"], list):
        raise ValueError("findings must be an array")
    for finding in data["findings"]:
        if not isinstance(finding, dict) or any(
            not isinstance(finding.get(field), str)
            for field in ("file", "issue", "why_it_matters")
        ) or type(finding.get("line")) is not int:
            raise ValueError("Invalid finding fields")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=Path("audit.jsonl"))
    ap.add_argument("--concurrency", type=int, default=4)
    ns = ap.parse_args()

    sem = asyncio.Semaphore(ns.concurrency)

    async def bounded(repo: Path) -> dict[str, Any]:
        async with sem:
            try:
                row = await audit_repo(repo)
            except Exception as exc:
                row = {"repo": repo.name, "error": "run_failed", "raw": str(exc)[:500]}
            head = subprocess.run(["git", "-C", str(repo.resolve()), "rev-parse", "HEAD"],
                                  capture_output=True, text=True)
            if head.returncode == 0:
                row["audited_commit"] = head.stdout.strip()
            return row

    results = await asyncio.gather(*(bounded(r) for r in ns.repos))
    failed = any("error" in row for row in results)
    destination = ns.out.with_suffix(".failed.jsonl") if failed else ns.out
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w") as fh:
        for row in results:
            fh.write(json.dumps(row) + "\n")

    flagged = sum(r.get("leakage") in {"suspected", "confirmed"} for r in results)
    print(f"audited {len(results)} repos; {flagged} flagged -> {destination}", file=sys.stderr)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
