"""Lightweight company research for personalized outreach."""

from __future__ import annotations

import os
import re

import httpx

from app.services.company.jobs import fetch_html


async def _serp_snippets(query: str, api_key: str, num: int = 6) -> list[str]:
    snippets: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                "https://serpapi.com/search.json",
                params={"engine": "google", "q": query, "num": num, "api_key": api_key},
            )
            if res.status_code != 200:
                return snippets
            for item in res.json().get("organic_results", []):
                t = item.get("title") or ""
                s = item.get("snippet") or ""
                if t or s:
                    snippets.append(f"{t}. {s}".strip())
    except Exception:
        pass
    return snippets


def _pick_angle(company_name: str, blobs: list[str]) -> str | None:
    keywords = (
        "ai",
        "machine learning",
        "genai",
        "llm",
        "platform",
        "payments",
        "fintech",
        "automation",
        "customer experience",
        "data",
        "cloud",
        "infrastructure",
        "product",
        "innovation",
        "unique",
        "leading",
        "first",
        "largest",
    )
    co = company_name.lower()
    best: str | None = None
    best_score = 0
    for blob in blobs:
        low = blob.lower()
        if co not in low and co.split()[0] not in low:
            continue
        score = sum(1 for k in keywords if k in low)
        if score > best_score and len(blob) > 40:
            best_score = score
            # Trim to one crisp sentence
            sentence = re.split(r"(?<=[.!?])\s+", blob.strip())[0]
            best = sentence[:220]
    return best


async def research_company_angle(
    company_name: str,
    domain: str | None = None,
) -> dict:
    """
    Find one specific company angle for outreach (product, strategy, tech bet).
  Uses SerpAPI + optional homepage skim. No invented facts beyond search text.
    """
    angle: str | None = None
    source = "general"
    blobs: list[str] = []

    serp_key = (os.getenv("SERPAPI_API_KEY") or "").strip()
    if serp_key:
        queries = [
            f'"{company_name}" product technology differentiation',
            f'"{company_name}" AI strategy OR platform OR innovation',
            f"what makes {company_name} different from competitors",
        ]
        for q in queries:
            blobs.extend(await _serp_snippets(q, serp_key))
        angle = _pick_angle(company_name, blobs)
        if angle:
            source = "web_search"

    d = (domain or "").replace("www.", "")
    if not angle and d:
        for url in (f"https://{d}/about", f"https://www.{d}/about", f"https://{d}"):
            html = await fetch_html(url, timeout=12.0)
            if not html:
                continue
            text = re.sub(r"\s+", " ", html)[:8000]
            blobs.append(text)
            angle = _pick_angle(company_name, [text])
            if angle:
                source = "company_website"
                break

    if not angle:
        angle = (
            f"{company_name}'s work in product and engineering — especially where data and "
            "applied technology meet customer impact"
        )
        source = "fallback"

    return {
        "companyAngle": angle,
        "angleSource": source,
        "researchSnippets": blobs[:5],
    }
