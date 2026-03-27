# testme.py
# Build and Test a Stateless MCP Server (Python)
# Pairs with mcp_plumber/testme.R
# Tim Fraser
#
# This script:
#   1–2) Handshake and list MCP tools
#   3)   Direct JSON-RPC: filter mtcars rows whose model name contains "toyota"
#   4)   Optional: same task via Ollama + filter_mtcars_by_model tool
#
# Start the server first:
#   cd 08_function_calling/mcp_fastapi && python runme.py

# 0. SETUP ###################################
print("# 0. SETUP ###################################")
print("Note: Run this script from the mcp_fastapi/ folder (or set paths accordingly).")

import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERVER = "http://127.0.0.1:8000/mcp"
# SERVER = "https://connect.systems-apps.com/fastapimcp/mcp"  # + CONNECT_API_KEY in .env

FILTER_SUBSTRING = "toyota"


def mcp_request(method, params=None, id=1):
    body = {"jsonrpc": "2.0", "id": id, "method": method, "params": params or {}}
    headers = {}
    api_key = os.getenv("CONNECT_API_KEY")
    if api_key:
        headers["Authorization"] = f"Key {api_key}"
    try:
        resp = requests.post(SERVER, json=body, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as exc:
        raise SystemExit(
            f"Cannot reach MCP server at {SERVER}.\n"
            "Start it first: cd 08_function_calling/mcp_fastapi && python runme.py\n"
            f"Original error: {exc}"
        ) from exc
    if not resp.ok:
        print(f"MCP HTTP {resp.status_code} body:\n{resp.text[:2000]}")
    resp.raise_for_status()
    return resp.json().get("result")


# 1. HANDSHAKE — initialize ##############################
print("# 1. HANDSHAKE — initialize ##############################")

init = mcp_request("initialize", {
    "protocolVersion": "2025-03-26",
    "clientInfo":      {"name": "py-test-client", "version": "0.1.0"},
    "capabilities":    {},
})

print(f"Server: {init['serverInfo']['name']} v {init['serverInfo']['version']}")

# 2. DISCOVER TOOLS — tools/list #########################
print("# 2. DISCOVER TOOLS — tools/list #########################")

tools = mcp_request("tools/list")
print("Available tools:")
for t in tools["tools"]:
    print(f"  - {t['name']}: {t['description']}")

# 3. CALL FILTER TOOL — Toyota rows in mtcars ############################
print("# 3. CALL A TOOL — filter_mtcars_by_model (contains 'toyota') ################")

result = mcp_request("tools/call", {
    "name":      "filter_mtcars_by_model",
    "arguments": {"contains": FILTER_SUBSTRING},
}, id=3)

rows_json = result["content"][0]["text"]
rows = json.loads(rows_json)
print(f"Rows matching {FILTER_SUBSTRING!r} (case-insensitive): {len(rows)}")
print(json.dumps(rows, indent=2))

# 4. OPTIONAL: Ollama chooses the same MCP tool ####################
print("# 4. CONNECT AN LLM TO THE MCP SERVER (filter Toyota) ####################")

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
CHAT_URL = f"{OLLAMA_BASE}/api/chat"
MODEL = "smollm2:1.7b"


def ollama_is_running():
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=2)
        return r.ok
    except requests.RequestException:
        return False


def mcp_to_ollama(tool):
    return {
        "type": "function",
        "function": {
            "name":        tool["name"],
            "description": tool["description"],
            "parameters":  tool["inputSchema"],
        },
    }


if not ollama_is_running():
    print(
        f"Skipping 4b–4d: no Ollama at {OLLAMA_BASE}.\n"
        "Start Ollama, then re-run — or set OLLAMA_HOST."
    )
else:
    tools_raw = mcp_request("tools/list", id=10)["tools"]
    # Only offer the filter tool so small models don’t pick summarize_dataset.
    filter_tools = [mcp_to_ollama(t) for t in tools_raw if t["name"] == "filter_mtcars_by_model"]

    print("# 4b. Ask the model to filter mtcars for Toyota ####################")
    messages = [{
        "role": "user",
        "content": (
            "Use the filter_mtcars_by_model tool exactly once. "
            f"Set contains to the string {FILTER_SUBSTRING!r} (lowercase) so we get all "
            "mtcars rows whose car model name includes Toyota, case-insensitive."
        ),
    }]

    body = {"model": MODEL, "messages": messages, "tools": filter_tools, "stream": False}
    resp = requests.post(CHAT_URL, json=body)
    resp.raise_for_status()
    result_llm = resp.json()

    print("# 4c. Forward tool_calls to MCP ####################")
    tool_calls = result_llm.get("message", {}).get("tool_calls", [])
    if not tool_calls:
        print("No tool_calls from the model — try a larger model or re-run.")
    else:
        tc = tool_calls[0]
        func_name = tc["function"]["name"]
        raw_args = tc["function"]["arguments"]
        func_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

        mcp_result = mcp_request(
            "tools/call",
            {"name": func_name, "arguments": func_args},
            id=11,
        )
        print(f"LLM chose: {func_name}({func_args})")
        print(mcp_result["content"][0]["text"])
