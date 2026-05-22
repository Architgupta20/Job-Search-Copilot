import json
import os
import re
from typing import Any

import httpx

import app.env  # noqa: F401 — load apps/web/.env
from app.env import get_groq_key, get_openai_key, get_llm_provider

RESUME_TAILOR_SYSTEM = """You tailor resumes to job descriptions WITHOUT lying.
The user will EDIT their own Word/DOCX file manually using your suggestions in the UI.

Rules:
- ONLY use facts from allowedClaims and originalResume. Never add employers, degrees, tools, certifications, dates, or metrics not present.
- Rephrase bullets and weave JD keywords ONLY when supported by existing facts.
- Unsupported JD terms go in keywordsSkipped — never invent experience.

Return JSON only:
{
  "jdTitle": string | null,
  "tailoredText": string (reference draft for copy/paste — section headers, one bullet per line with "- "),
  "suggestedEdits": [
    {
      "section": string,
      "original": string (short excerpt from resume),
      "suggested": string (rewritten bullet or sentence),
      "reason": string (which JD keywords this supports)
    }
  ],
  "keywordsUsed": string[],
  "keywordsSkipped": string[],
  "changeSummary": string[]
}

Provide at least 5 suggestedEdits when possible. tailoredText is a readable draft, NOT a file merge."""


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text.strip()


def _groq_key() -> str:
    return get_groq_key()


def _openai_key() -> str:
    return get_openai_key()


def _provider() -> str:
    forced = get_llm_provider()
    if forced == "gemini":
        raise ValueError(
            "Python agents: use groq, openai, or ollama. "
            "For no API key, set LLM_PROVIDER=ollama and run: ollama pull llama3.2"
        )
    if forced == "ollama":
        return "ollama"
    if forced in ("groq", "openai"):
        if forced == "groq" and not _groq_key():
            raise ValueError("LLM_PROVIDER=groq but GROQ_API_KEY is missing in apps/web/.env")
        if forced == "openai" and not _openai_key():
            raise ValueError("LLM_PROVIDER=openai but OPENAI_API_KEY is missing in apps/web/.env")
        return forced
    if _groq_key():
        return "groq"
    if _openai_key():
        return "openai"
    raise ValueError(
        "Set GROQ_API_KEY, OPENAI_API_KEY, or LLM_PROVIDER=ollama in apps/web/.env"
    )


async def _ollama_json(system: str, user: str) -> dict[str, Any]:
    base = (os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    url = f"{base}/api/chat"
    async with httpx.AsyncClient(timeout=300.0) as client:
        res = await client.post(
            url,
            json={
                "model": model,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        res.raise_for_status()
        data = res.json()
        raw = data.get("message", {}).get("content", "")
        return json.loads(_extract_json(raw))


async def llm_json_completion(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    provider = _provider()
    user = json.dumps(user_payload)

    if provider == "ollama":
        try:
            return await _ollama_json(system, user)
        except httpx.ConnectError:
            raise ValueError(
                "Ollama not running. Install from https://ollama.com, then: ollama pull llama3.2 && ollama serve"
            ) from None
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Ollama error ({e.response.status_code}): {e.response.text[:300]}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Ollama returned invalid JSON: {e}") from e

    if provider == "groq":
        key = _groq_key()
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    else:
        key = _openai_key()
        url = "https://api.openai.com/v1/chat/completions"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            res.raise_for_status()
            data = res.json()
            raw = data["choices"][0]["message"]["content"]
            try:
                return json.loads(_extract_json(raw))
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM returned invalid JSON: {e}") from e
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500]
        if e.response.status_code == 401 and provider == "groq":
            raise ValueError(
                "Groq rejected your API key (401). Save a NEW key in apps/web/.env with nano, "
                "or switch to Ollama: LLM_PROVIDER=ollama (see README). Details: " + body
            ) from e
        if provider == "groq" and (
            e.response.status_code == 400
            and (
                "organization_restricted" in body
                or "Organization has been restricted" in body
            )
        ):
            raise ValueError(
                "Groq restricted your account (organization_restricted). "
                "Open https://console.groq.com and contact Groq support, or switch LLM in apps/web/.env: "
                "LLM_PROVIDER=ollama (free, local) or LLM_PROVIDER=openai with OPENAI_API_KEY."
            ) from e
        raise ValueError(f"LLM API error ({e.response.status_code}): {body}") from e
    except httpx.RequestError as e:
        raise ValueError(f"LLM request failed: {e}") from e


async def tailor_resume_llm(payload: dict[str, Any]) -> dict[str, Any]:
    return await llm_json_completion(RESUME_TAILOR_SYSTEM, payload)
