"""Deterministic auditor checks; these do not invoke an LLM."""
import asyncio
import copy
import json

import pandas as pd
import pytest

from agent.audit import check_identity, validate_report


@pytest.mark.parametrize("suffix", [".csv", ".parquet"])
def test_identity_tool_reads_both_table_formats(tmp_path, suffix):
    frame = pd.DataFrame({"a": [1, 4, 2, 8, 3], "b": [5, 2, 9, 1, 7]})
    frame["cnt"] = frame.a + frame.b
    path = tmp_path / ("features" + suffix)
    if suffix == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)
    result = asyncio.run(check_identity.handler({
        "csv_path": str(path), "target": "cnt", "candidates": ["a", "b"]
    }))
    report = json.loads(result["content"][0]["text"])
    assert report["verdict"] == "LEAKAGE"
    assert any(hit["columns"] == ["a", "b"] for hit in report["identities"])


def test_report_rejects_missing_fields_and_non_boolean_verdicts():
    with pytest.raises(ValueError):
        validate_report({"repo": "example"})
    valid = {"repo": "example", "leakage": "none", "temporal_ok": True,
             "baseline_reported": True, "reproducible": True,
             "findings": [], "confidence": "low"}
    validate_report(valid)
    invalid = copy.deepcopy(valid)
    invalid["temporal_ok"] = "yes"
    with pytest.raises(ValueError, match="must be boolean"):
        validate_report(invalid)
