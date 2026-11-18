#!/usr/bin/env bash
# `make check-model`: is the local agent model ready for Claude Code?
# Exits non-zero with a plain explanation if not. Run this before `claude`.
set -uo pipefail

MODEL="${MODEL:-bikeshare-coder}"
HOST="${OLLAMA_HOST:-http://localhost:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "FAIL: ollama is not installed. See https://ollama.com/download" >&2; exit 1
fi
if ! curl -fsS "$HOST/api/tags" >/dev/null 2>&1; then
  echo "FAIL: no Ollama server at $HOST. Start it with: ollama serve" >&2; exit 1
fi
if ! ollama show "$MODEL" >/dev/null 2>&1; then
  echo "FAIL: model '$MODEL' not built. Run: make model" >&2; exit 1
fi

ctx=$(ollama show "$MODEL" 2>/dev/null | awk '/num_ctx/ {print $2}' | head -1)
if [ -z "$ctx" ] || [ "$ctx" -lt 65536 ]; then
  echo "FAIL: '$MODEL' has num_ctx=${ctx:-unset}; need >= 65536. Rebuild with: make model" >&2; exit 1
fi
if ! ollama show "$MODEL" 2>/dev/null | grep -qi "tools"; then
  echo "WARN: '$MODEL' does not advertise tool support; Claude Code needs it." >&2
fi

# Check that the model returns a real ping tool call.
payload=$(python -c '
import json, sys
print(json.dumps({
    "model": sys.argv[1],
    "max_tokens": 1024,
    "thinking": {"type": "disabled"},
    "tools": [{
        "name": "ping",
        "description": "Call this tool to check connectivity.",
        "input_schema": {"type":"object","properties":{}}
    }],
    "messages": [{
        "role": "user",
        "content": "Call the ping tool now."
    }]
}))
' "$MODEL") || exit 1

if resp=$(curl -fsS --max-time 180 "$HOST/v1/messages" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ollama" \
    -H "anthropic-version: 2023-06-01" \
    --data-binary "$payload"); then
    :
else
    curl_status=$?
    echo "FAIL: model request failed (curl exit $curl_status)." >&2
    exit 1
fi

if ! printf '%s' "$resp" | python -c '
import json, sys
try:
    result = json.load(sys.stdin)
except (ValueError, UnicodeError) as exc:
    print(f"FAIL: invalid JSON response: {exc}", file=sys.stderr)
    sys.exit(1)

blocks = result.get("content") if isinstance(result, dict) else None
ok = isinstance(blocks, list) and any(
    isinstance(block, dict)
    and block.get("type") == "tool_use"
    and block.get("name") == "ping"
    for block in blocks
)
if not ok:
    print("FAIL: response contains no ping tool_use block.", file=sys.stderr)
    sys.exit(1)
'; then
    exit 1
fi

echo "OK model: $MODEL at $HOST, num_ctx=$ctx, ping tool call returned."
