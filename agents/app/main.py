# Load apps/web/.env before routers or LLM client import os.environ
import app.env  # noqa: F401

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.env import (
    WEB_ENV_FILE,
    get_env_path,
    get_groq_key,
    get_hunter_key,
    get_llm_provider,
    get_openai_key,
    get_serpapi_key,
    is_serpapi_disabled,
    serpapi_available,
)
from app.routers import company, cover_letter, interview_prep, jd, resume
from app.services.llm.client import _provider

app = FastAPI(
    title="Job Search Copilot Agents",
    description="Python agents for resume, company search, and JD tailoring.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(company.router)
app.include_router(jd.router)
app.include_router(cover_letter.router)
app.include_router(interview_prep.router)


@app.on_event("startup")
def startup_log_env():
    path = get_env_path()
    key = get_groq_key()
    print(f"[agents] env file: {path or 'MISSING — create apps/web/.env'}")
    print(f"[agents] LLM_PROVIDER: {get_llm_provider() or '(not set)'}")
    print(f"[agents] GROQ_API_KEY loaded: {bool(key)} (length {len(key)})")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agents",
        "envFile": str(WEB_ENV_FILE) if WEB_ENV_FILE.is_file() else None,
    }


@app.get("/health/services")
def health_services():
    """Which integrations are configured (no secrets returned)."""
    provider = get_llm_provider() or "groq"
    groq_ok = bool(get_groq_key())
    llm_ready = provider == "ollama" or (provider == "groq" and groq_ok) or (
        provider == "openai" and bool(get_openai_key())
    )
    serp_key = bool(get_serpapi_key())
    serp_disabled = is_serpapi_disabled()
    return {
        "llm": {
            "provider": provider,
            "configured": llm_ready,
        },
        "serpapi": {
            "configured": serp_key,
            "disabled": serp_disabled,
            "available": serpapi_available(),
        },
        "hunter": {
            "configured": bool(get_hunter_key()),
        },
    }


@app.get("/health/llm")
async def health_llm():
    """Check Groq key from apps/web/.env (no secret returned)."""
    try:
        provider = _provider()
        key = get_groq_key()
        env_path = get_env_path()

        if not env_path:
            return {
                "ok": False,
                "error": f"Missing {WEB_ENV_FILE} — create apps/web/.env",
            }
        if provider != "groq":
            return {"ok": False, "provider": provider, "error": "Expected LLM_PROVIDER=groq"}
        if not key:
            return {
                "ok": False,
                "envFile": str(env_path),
                "error": "GROQ_API_KEY empty in apps/web/.env",
            }
        if not key.startswith("gsk_"):
            return {
                "ok": False,
                "envFile": str(env_path),
                "error": "Key should start with gsk_",
                "keyLength": len(key),
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
        if res.status_code == 401:
            return {
                "ok": False,
                "envFile": str(env_path),
                "keyLength": len(key),
                "error": (
                    "Groq rejected this API key. The app IS reading .env — "
                    "create a NEW key at console.groq.com/keys and update apps/web/.env"
                ),
            }
        res.raise_for_status()
        return {
            "ok": True,
            "provider": "groq",
            "envFile": str(env_path),
            "keyLength": len(key),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
