"""Deterministic auditor checks; these do not invoke an LLM."""
import asyncio
import copy
import json

import pandas as pd
import pytest

from agent.audit import audit_options, check_identity, save_results, validate_report


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


def test_local_audit_explicitly_disables_thinking_and_bounds_responses(tmp_path):
    options = audit_options(tmp_path)
    assert options.thinking == {"type": "disabled"}
    assert json.loads(options.env["CLAUDE_CODE_EXTRA_BODY"]) == {"thinking": {"type": "disabled"}}
    assert options.env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "4096"
    assert options.env["CLAUDE_CODE_MAX_CONTEXT_TOKENS"] == "65536"
    assert json.loads(options.settings)["env"] == options.env
    assert options.strict_mcp_config


def test_failure_is_counted_and_previous_evidence_is_preserved(tmp_path, capsys):
    out = tmp_path / "audit.jsonl"
    out.write_text('existing successful audit\n')
    previous = out.with_suffix('.failed.jsonl')
    previous.write_text('previous failed attempt\n')
    failures = save_results([{"repo": "example", "error": "run_failed", "raw": "output limit"}], out)
    assert failures == 1
    assert out.read_text() == 'existing successful audit\n'
    archived = list(tmp_path.glob('audit.failed-*.jsonl'))
    assert len(archived) == 1 and archived[0].read_text() == 'previous failed attempt\n'
    assert json.loads(previous.read_text())["error"] == "run_failed"
    assert 'completed 0; failed 1' in capsys.readouterr().err


def test_sdk_sends_explicit_controls_to_http_endpoint(tmp_path):
    """Inspect the bundled CLI's HTTP request; no LLM or real audit is run."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from claude_agent_sdk import ResultError, query

    captured = []

    class Probe(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            captured.append({key: body.get(key) for key in ("model", "max_tokens", "thinking")})
            response = json.dumps({"type": "error", "error": {
                "type": "invalid_request_error", "message": "Expected local request probe"
            }}).encode()
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Probe)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    async def inspect_request():
        options = audit_options(tmp_path)
        options.setting_sources = []
        options.tools = []
        options.mcp_servers = {}
        options.allowed_tools = []
        options.max_turns = 1
        options.env.update({
            "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}",
            "ANTHROPIC_AUTH_TOKEN": "ollama", "ANTHROPIC_API_KEY": "",
            "CLAUDE_CONFIG_DIR": str(tmp_path / "claude-config"),
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        })
        options.settings = json.dumps({"env": options.env})
        try:
            async for message in query(prompt="Synthetic request-control probe.", options=options):
                pass
        except ResultError as exc:
            assert "Expected local request probe" in str(exc)

    try:
        asyncio.run(asyncio.wait_for(inspect_request(), timeout=25))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert captured
    assert all(item["thinking"] == {"type": "disabled"} for item in captured)
    assert all(item["max_tokens"] == 4096 for item in captured)
    print("Captured SDK request controls:", json.dumps(captured))
