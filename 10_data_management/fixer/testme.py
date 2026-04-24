# testme.py
# Smoke test Ollama Cloud chat from the fixer folder (no tools)
# Tim Fraser

from __future__ import annotations

import os
import sys

import httpx

from pathlib import Path

_FIXER_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_FIXER_ROOT))


def resolve_fixer_root() -> Path:
    r = os.environ.get("FIXER_ROOT", "").strip()
    if r and Path(r).is_dir():
        return Path(r).resolve()
    wd = Path.cwd().resolve()
    if (wd / "functions.py").is_file() or (wd / "functions.R").is_file():
        return wd
    cand = wd / "10_data_management" / "fixer"
    if (cand / "functions.py").is_file():
        return cand.resolve()
    raise SystemExit("Run from fixer/, dsai repo root, or set FIXER_ROOT.")


from functions import load_fixer_dotenv, normalize_ollama_api_key, ollama_chat_once

FIXER_ROOT = resolve_fixer_root()
repo_env = FIXER_ROOT.parent.parent / ".env"
fixer_env = FIXER_ROOT / ".env"
if not fixer_env.is_file() and not repo_env.is_file():
    raise SystemExit(
        "No .env found. Put OLLAMA_API_KEY in 10_data_management/fixer/.env or in the repo root .env "
        "(next to this course repo). Copy fixer/.env.example to fixer/.env if needed."
    )
load_fixer_dotenv(FIXER_ROOT)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com").strip()
OLLAMA_API_KEY = normalize_ollama_api_key(os.environ.get("OLLAMA_API_KEY", ""))
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "").strip()
if not OLLAMA_MODEL:
    OLLAMA_MODEL = "gpt-oss:120b"

if not OLLAMA_API_KEY:
    raise SystemExit(
        "OLLAMA_API_KEY is empty after loading .env. Set it in repo root .env or fixer/.env "
        "(variable name must be OLLAMA_API_KEY)."
    )

messages = [
    {"role": "user", "content": "Reply with exactly one word: pong"},
]

print(f"Test query: POST {OLLAMA_HOST}/api/chat")
print(f"Model: {OLLAMA_MODEL}\n")

try:
    out = ollama_chat_once(
        OLLAMA_HOST,
        OLLAMA_API_KEY,
        OLLAMA_MODEL,
        messages,
        tools=None,
        format=None,
        max_output_tokens=None,
    )
except Exception as e:
    try:
        # httpx stores last response on exception in some cases
        if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
            print("HTTP status:", e.response.status_code)
            print("Response body:\n", e.response.text)
    except Exception:
        pass
    raise SystemExit(str(e)) from e

print("Assistant content:\n", out.get("content", ""), "\n", sep="")
print("Smoke test OK.")
