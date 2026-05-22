import json
import os
import re
from typing import Any

import httpx

RESUME_TAILOR_SYSTEM = """You tailor resumes to job descriptions WITHOUT lying.
Rules:
- ONLY use facts from allowedClaims and originalResume. Never add employers, degrees, tools, certifications, dates, or metrics not present.
- You may rephrase bullets, reorder sections, and weave JD keywords ONLY when supported by existing facts.
- If a JD keyword has no support, put it in keywordsSkipped — do not invent experience.

CRITICAL FORMAT for tailoredText (Word export):
- Keep the SAME section order and section headings as originalResume.
- ONE line per paragraph: each bullet on its own line starting with "- ".
- Put a BLANK LINE between major sections.
- Section headers on their own line (e.g. "WORK EXPERIENCE:").
- Do NOT merge the resume into one giant paragraph.
- Plain text only, no markdown.

Return JSON only:
{
  "jdTitle": string | null,
  "tailoredText": string,
  "keywordsUsed": string[],
  "keywordsSkipped": string[],
  "changeSummary": string[]
}"""


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
    return (os.getenv("GROQ_API_KEY") or "").strip()


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def _provider() -> str:
    forced = (os.getenv("LLM_PROVIDER") or "").lower()
    if forced in ("groq", "openai", "gemini"):
        return forced
    if _groq_key():
        return "groq"
    if _openai_key():
        return "openai"
    raise ValueError(
        "Add GROQ_API_KEY or OPENAI_API_KEY to apps/web/.env (see README)."
    )


async def llm_json_completion(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    provider = _provider()
    user = json.dumps(user_payload)

    if provider == "groq":
        key = _groq_key()
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    else:
        key = _openai_key()
        url = "https://api.openai.com/v1/chat/completions"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
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
        return json.loads(_extract_json(raw))


async def tailor_resume_llm(payload: dict[str, Any]) -> dict[str, Any]:
    return await llm_json_completion(RESUME_TAILOR_SYSTEM, payload)
