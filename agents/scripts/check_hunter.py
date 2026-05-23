#!/usr/bin/env python3
"""Run: conda activate job-copilot && python scripts/check_hunter.py"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.env  # noqa: E402
from app.env import WEB_ENV_FILE, get_hunter_key


def main() -> int:
    print(f"Env file: {WEB_ENV_FILE}")
    key = get_hunter_key()
    if not key:
        print("FAIL — HUNTER_API_KEY is missing in apps/web/.env")
        return 1

    print(f"Key loaded (length {len(key)})")

    try:
        res = httpx.get(
            "https://api.hunter.io/v2/account",
            params={"api_key": key},
            timeout=20.0,
        )
    except httpx.RequestError as e:
        print(f"FAIL — network error: {e}")
        return 1

    if res.status_code != 200:
        print(f"FAIL — Hunter returned {res.status_code}: {res.text[:300]}")
        return 1

    data = res.json().get("data") or {}
    email = data.get("email", "?")
    plan = data.get("plan_name", "?")
    remaining = data.get("requests", {}).get("searches", {}).get("available", "?")
    print(f"SUCCESS — Hunter accepts this key.")
    print(f"  Account: {email}")
    print(f"  Plan: {plan}")
    print(f"  Search credits available: {remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
