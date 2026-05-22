#!/usr/bin/env python3
"""Run: conda activate job-copilot && python scripts/check_groq.py"""

import hashlib
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.env  # noqa: E402
from app.env import WEB_ENV_FILE, get_groq_key, get_llm_provider


def read_key_from_file() -> str:
    if not WEB_ENV_FILE.is_file():
        return ""
    for line in WEB_ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def key_fingerprint(key: str) -> str:
    if not key:
        return "(empty)"
    h = hashlib.sha256(key.encode()).hexdigest()[:12]
    return f"sha256:{h} prefix={key[:8]}... suffix=...{key[-4:]}"


ENV_FILE = WEB_ENV_FILE
REPO = ENV_FILE.parent.parent.parent

print(f"Repo:     {REPO}")
print(f"Env file: {ENV_FILE}")
print(f"Exists:   {ENV_FILE.is_file()}")

if not ENV_FILE.is_file():
    print("\nERROR: apps/web/.env is missing.")
    sys.exit(1)

file_key = read_key_from_file()
env_key = get_groq_key()

print(f"\nLLM_PROVIDER: {get_llm_provider()!r}")
print(f"Key from FILE:  loaded={bool(file_key)} {key_fingerprint(file_key)}")
print(f"Key from APP:   loaded={bool(env_key)} {key_fingerprint(env_key)}")

if file_key != env_key:
    print("\nWARNING: File and app keys differ — restart terminal / unset GROQ_API_KEY")

key = env_key or file_key
if not key:
    print("\nERROR: GROQ_API_KEY is empty in apps/web/.env")
    sys.exit(1)

bad = [c for c in key if ord(c) > 127 or c in "\n\r\t"]
if bad:
    print(f"\nWARNING: Key has unusual characters: {bad!r} — re-type the key in nano")

if not key.startswith("gsk_"):
    print("\nERROR: Key should start with gsk_")
    sys.exit(1)

print(f"Key length: {len(key)} (typical Groq keys: 50–60 chars)")

r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=20,
)
print(f"\nGroq API status: {r.status_code}")
if r.status_code == 200:
    print("SUCCESS — Groq accepts this key.")
    sys.exit(0)

print(r.text[:400])
print(
    "\nFAIL — Groq rejected this exact key."
    "\n"
    "\nIf you created new keys but fingerprint above is UNCHANGED, you did not save apps/web/.env:"
    "\n  nano ~/Desktop/Job-Search-copilot/apps/web/.env"
    "\n"
    "\nOr test in Terminal (paste key when prompted, not saved to disk):"
    "\n  read -s GROQ_TEST_KEY && echo"
    "\n  curl -s -o /dev/null -w '%{http_code}\\n' https://api.groq.com/openai/v1/models \\"
    "\n    -H \"Authorization: Bearer $GROQ_TEST_KEY\""
    "\n"
    "\nIf curl is also 401, the problem is Groq account/key — not this app."
    "\nWorkaround: use Ollama (free, local) — see agents/README.md"
)
sys.exit(1)
