"""
Load apps/web/.env before any other app code runs.
Import this module first (main.py does) so API keys are always available.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

# agents/app/env.py -> repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ENV_FILE = REPO_ROOT / "apps" / "web" / ".env"
ROOT_ENV_FILE = REPO_ROOT / ".env"

# Always prefer values from apps/web/.env for these keys
_KEYS_FROM_WEB_ENV = frozenset(
    {
        "GROQ_API_KEY",
        "OPENAI_API_KEY",
        "LLM_PROVIDER",
        "GROQ_MODEL",
        "OPENAI_MODEL",
        "OLLAMA_MODEL",
        "OLLAMA_BASE_URL",
        "SERPAPI_API_KEY",
        "SERPAPI_DISABLED",
        "HUNTER_API_KEY",
    }
)


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip('"').strip("'").strip()


def load_web_env() -> Path | None:
    """Load apps/web/.env into os.environ. Returns path if file exists."""
    if not WEB_ENV_FILE.is_file():
        return None

    # utf-8-sig removes BOM if present
    values = dotenv_values(WEB_ENV_FILE, encoding="utf-8-sig")
    for key, raw in values.items():
        if not key or raw is None:
            continue
        val = _clean(raw)
        if key in _KEYS_FROM_WEB_ENV or not os.environ.get(key):
            os.environ[key] = val

    return WEB_ENV_FILE


def load_root_env() -> None:
    """Optional repo-root .env — does not override apps/web/.env keys."""
    if not ROOT_ENV_FILE.is_file():
        return
    values = dotenv_values(ROOT_ENV_FILE, encoding="utf-8-sig")
    for key, raw in values.items():
        if not key or raw is None:
            continue
        if key in _KEYS_FROM_WEB_ENV:
            continue
        if not os.environ.get(key):
            os.environ[key] = _clean(raw)


def get_env_path() -> Path | None:
    return WEB_ENV_FILE if WEB_ENV_FILE.is_file() else None


def get_groq_key() -> str:
    return _clean(os.environ.get("GROQ_API_KEY"))


def get_openai_key() -> str:
    return _clean(os.environ.get("OPENAI_API_KEY"))


def get_llm_provider() -> str:
    return _clean(os.environ.get("LLM_PROVIDER")).lower()


def get_hunter_key() -> str:
    return _clean(os.environ.get("HUNTER_API_KEY"))


def get_serpapi_key() -> str:
    return _clean(os.environ.get("SERPAPI_API_KEY"))


def is_serpapi_disabled() -> bool:
    return _clean(os.environ.get("SERPAPI_DISABLED")).lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def serpapi_available() -> bool:
    return bool(get_serpapi_key()) and not is_serpapi_disabled()


# Load on import
_loaded_path = load_web_env()
load_root_env()
