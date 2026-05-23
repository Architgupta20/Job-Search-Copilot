"""Deep contact lookup: Hunter.io, web search, company pages."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.env import get_hunter_key
from app.services.company.contact_hints import contact_lookup_hints
from app.services.company.jobs import fetch_html

EMAIL_RE = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
)

JUNK_EMAIL_PARTS = (
    "noreply",
    "no-reply",
    "donotreply",
    "support@",
    "info@",
    "hello@",
    "contact@",
    "careers@",
    "jobs@",
    "hr@",
    "recruiting@",
    "news@",
    "press@",
    "linkedin.com",
    "example.com",
    "sentry.io",
    "wixpress.com",
    "schema.org",
)


def _clean_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    d = domain.lower().replace("www.", "").strip()
    return d or None


def _name_parts(full_name: str) -> tuple[str, str]:
    parts = [p for p in full_name.strip().split() if p]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    if parts:
        return parts[0], parts[0]
    return "", ""


def _email_ok(email: str, domain: str | None, person_name: str, *, from_hunter: bool = False) -> bool:
    low = email.lower()
    if any(j in low for j in JUNK_EMAIL_PARTS):
        return False
    if from_hunter:
        return True
    first, last = _name_parts(person_name)
    local = low.split("@")[0]
    if first and first.lower() not in local and last and last.lower() not in local:
        if domain and domain in low.split("@")[-1]:
            return True
        return False
    return True


def _pick_best_candidate(candidates: list[dict]) -> tuple[str | None, str | None, str]:
    if not candidates:
        return None, None, "not_found"
    ranked = sorted(
        candidates,
        key=lambda c: (
            2 if c.get("confidence") == "verified" else 1 if c.get("confidence") == "likely" else 0,
            c.get("score") or 0,
        ),
        reverse=True,
    )
    best = ranked[0]
    email = best.get("email")
    phone = best.get("phone")
    conf = best.get("confidence") or "likely"
    return email, phone, conf


async def _hunter_email_finder(
    domain: str,
    first: str,
    last: str,
    api_key: str,
) -> dict | None:
    if not first or not domain:
        return None
    try:
        async with httpx.AsyncClient(timeout=18.0) as client:
            res = await client.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "domain": domain,
                    "first_name": first,
                    "last_name": last,
                    "api_key": api_key,
                },
            )
            if res.status_code != 200:
                return None
            data = res.json().get("data") or {}
            email = data.get("email")
            if not email:
                return None
            score = data.get("score") or 0
            conf = "verified" if score >= 85 else "likely"
            out: dict[str, Any] = {
                "email": email,
                "source": "Hunter.io",
                "confidence": conf,
                "score": score,
                "detail": f"Email finder score {score}",
            }
            if data.get("phone_number"):
                out["phone"] = data["phone_number"]
            return out
    except Exception:
        return None


async def _hunter_domain_search(
    domain: str,
    person_name: str,
    api_key: str,
) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=18.0) as client:
            res = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": 20},
            )
            if res.status_code != 200:
                return None
            emails = res.json().get("data", {}).get("emails") or []
            first, last = _name_parts(person_name)
            for row in emails:
                val = row.get("value") or ""
                fn = (row.get("first_name") or "").lower()
                ln = (row.get("last_name") or "").lower()
                if fn == first.lower() and ln == last.lower():
                    return {
                        "email": val,
                        "source": "Hunter.io (domain directory)",
                        "confidence": "likely",
                        "score": row.get("confidence") or 70,
                        "detail": row.get("position") or "Domain search match",
                    }
    except Exception:
        pass
    return None


def _extract_emails_from_text(text: str, domain: str | None, person_name: str) -> list[str]:
    found: list[str] = []
    for m in EMAIL_RE.findall(text):
        if _email_ok(m, domain, person_name):
            found.append(m)
    return list(dict.fromkeys(found))


async def _serp_contact_search(
    person_name: str,
    company_name: str,
    domain: str | None,
    api_key: str,
) -> list[dict]:
    candidates: list[dict] = []
    queries = [
        f'"{person_name}" "{company_name}" email',
        f'"{person_name}" email contact',
    ]
    d = _clean_domain(domain)
    if d:
        queries.insert(0, f'site:{d} "{person_name}" email')

    try:
        async with httpx.AsyncClient(timeout=22.0) as client:
            for q in queries[:3]:
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={"engine": "google", "q": q, "num": 8, "api_key": api_key},
                )
                if res.status_code != 200:
                    continue
                for item in res.json().get("organic_results", []):
                    blob = f"{item.get('title', '')} {item.get('snippet', '')}"
                    for email in _extract_emails_from_text(blob, d, person_name):
                        candidates.append({
                            "email": email,
                            "source": "Google search (SerpAPI)",
                            "confidence": "likely",
                            "score": 60,
                            "detail": f"Found in search snippet for: {q[:60]}",
                        })
                    link = item.get("link")
                    if link and d and d in (link or "").lower():
                        candidates.append({
                            "email": None,
                            "source": "Google search (SerpAPI)",
                            "confidence": "not_found",
                            "score": 0,
                            "detail": link,
                            "pageUrl": link,
                        })
    except Exception:
        pass
    return candidates


async def _scrape_pages_for_contact(
    page_urls: list[str],
    domain: str | None,
    person_name: str,
) -> list[dict]:
    candidates: list[dict] = []
    seen_pages: set[str] = set()
    for url in page_urls[:4]:
        if url in seen_pages:
            continue
        seen_pages.add(url)
        html = await fetch_html(url, timeout=14.0)
        if not html:
            continue
        name_low = person_name.lower()
        if name_low.split()[0] not in html.lower() and name_low not in html.lower():
            continue
        for email in _extract_emails_from_text(html, domain, person_name):
            candidates.append({
                "email": email,
                "source": "Company / web page",
                "confidence": "likely",
                "score": 75,
                "detail": url[:120],
            })
        for m in PHONE_RE.findall(html):
            if len(m.replace("-", "").replace(" ", "")) >= 10:
                candidates.append({
                    "phone": m,
                    "source": "Company / web page",
                    "confidence": "likely",
                    "score": 50,
                    "detail": url[:120],
                })
                break
    return candidates


async def enrich_person_contact(
    person: dict,
    company_name: str,
    domain: str | None,
) -> dict:
    """Run Hunter + SerpAPI + page scrape; attach email/phone and research log."""
    d = _clean_domain(domain)
    first, last = _name_parts(person.get("name", ""))
    sources_checked: list[str] = []
    candidates: list[dict] = []
    page_urls: list[str] = []

    hunter_key = get_hunter_key()
    serp_key = (os.getenv("SERPAPI_API_KEY") or "").strip()

    if hunter_key and d:
        sources_checked.append("Hunter.io")
        found = await _hunter_email_finder(d, first, last, hunter_key)
        if found:
            candidates.append(found)
        if not any(c.get("email") for c in candidates):
            domain_hit = await _hunter_domain_search(d, person.get("name", ""), hunter_key)
            if domain_hit:
                candidates.append(domain_hit)

    if serp_key:
        sources_checked.append("Google / SerpAPI")
        serp_hits = await _serp_contact_search(
            person.get("name", ""), company_name, d, serp_key
        )
        for hit in serp_hits:
            if hit.get("email"):
                candidates.append(hit)
            elif hit.get("pageUrl"):
                page_urls.append(hit["pageUrl"])

    if d:
        sources_checked.append("Company website")
        for path in (f"https://{d}/about", f"https://www.{d}/team", f"https://{d}/team"):
            page_urls.append(path)

    if page_urls:
        scrape_hits = await _scrape_pages_for_contact(page_urls, d, person.get("name", ""))
        candidates.extend(scrape_hits)

    # Dedupe emails
    seen_emails: set[str] = set()
    unique: list[dict] = []
    for c in candidates:
        em = (c.get("email") or "").lower()
        if em and em in seen_emails:
            continue
        if em:
            seen_emails.add(em)
        unique.append(c)

    email, phone, conf = _pick_best_candidate(unique)
    if not email:
        conf = "not_found"
    elif conf == "not_found":
        conf = "likely"

    person["email"] = email or person.get("email")
    person["phone"] = phone or person.get("phone")
    person["emailConfidence"] = conf if email else person.get("emailConfidence", "not_found")
    if phone:
        person["phoneConfidence"] = "likely"

    person["contactResearch"] = {
        "sourcesChecked": sources_checked or ["No API keys — add HUNTER_API_KEY or SERPAPI_API_KEY"],
        "candidates": unique[:8],
    }

    if not email:
        person["contactHints"] = contact_lookup_hints(
            company_name, person.get("name", ""), d
        )
    else:
        person.pop("contactHints", None)

    return person


async def enrich_people_contacts(
    people: list[dict],
    company_name: str,
    domain: str | None,
) -> list[dict]:
    sem = asyncio.Semaphore(4)

    async def one(p: dict) -> dict:
        async with sem:
            return await enrich_person_contact(p, company_name, domain)

    return list(await asyncio.gather(*[one(p) for p in people]))
