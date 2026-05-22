"""Company intelligence, people discovery, and jobs — Python agents."""

import json
import os
import re
import uuid
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import RUNS_DIR
from app.services.llm.client import llm_json_completion

USER_AGENT = "JobSearchCopilot/1.0 (local recruiter tool)"
PEOPLE_QUERY = (
    '("Lead AI Engineer" OR "Program Manager" OR CEO OR "Head of AI" '
    '"Engineering Manager" OR "Technical Recruiter" OR "Talent Acquisition")'
)

ROLE_PATTERNS = {
    "AI Engineer": re.compile(
        r"ai engineer|gen\s*ai|generative ai|llm|machine learning engineer|ml engineer",
        re.I,
    ),
    "ML Engineer": re.compile(r"ml engineer|machine learning engineer|mlops", re.I),
    "Data Scientist": re.compile(r"data scientist|applied scientist", re.I),
    "Data Analyst": re.compile(r"data analyst|analytics engineer", re.I),
}


async def _fetch_html(url: str, timeout: float = 12.0) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            res = await client.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            if res.status_code >= 400:
                return None
            if "text/html" not in res.headers.get("content-type", ""):
                return None
            return res.text
    except Exception:
        return None


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


async def resolve_company(name: str) -> dict:
    trimmed = name.strip()
    words = re.sub(r"[^a-z0-9\s]", "", trimmed.lower()).split()
    slugs = {_slugify(trimmed), words[0] if words else "", "".join(words[:2])}
    hosts = []
    for s in slugs:
        if not s:
            continue
        hosts.extend([f"https://www.{s}.com", f"https://{s}.com", f"https://www.{s}.io"])

    domain = None
    careers_url = None
    for host in dict.fromkeys(hosts):
        html = await _fetch_html(host)
        if not html:
            continue
        domain = urlparse(host).hostname
        for path in ["/careers", "/jobs", "/join-us", "/company/careers"]:
            u = urljoin(host, path)
            sub = await _fetch_html(u)
            if sub and ("job" in sub.lower() or "career" in sub.lower()):
                careers_url = u
                break
        if not careers_url:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                t = (a.get_text() or "").lower()
                if "career" in t or "job" in t:
                    careers_url = urljoin(host, a["href"])
                    break
        if domain:
            break

    return {"name": trimmed, "domain": domain, "careersUrl": careers_url}


async def fetch_jobs(careers_url: str, roles: list[str]) -> list[dict]:
    html = await _fetch_html(careers_url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    base = careers_url
    seen: set[str] = set()
    jobs: list[dict] = []
    for a in soup.find_all("a", href=True):
        title = re.sub(r"\s+", " ", a.get_text()).strip()
        if len(title) < 8 or len(title) > 120:
            continue
        url = urljoin(base, a["href"])
        if url in seen:
            continue
        score = 0
        for role in roles:
            pat = ROLE_PATTERNS.get(role)
            if pat and pat.search(title):
                score += 10
        if score < 8:
            continue
        seen.add(url)
        jobs.append({"title": title, "url": url, "location": None, "snippet": None, "matchScore": score})
    jobs.sort(key=lambda j: j["matchScore"], reverse=True)
    return jobs[:15]


def _person_works_at_company(serp_title: str, snippet: str, company: str) -> bool:
    aliases = {company.lower().strip()}
    aliases.add(re.sub(r"\b(inc|llc|ltd|corp)\b\.?", "", company.lower()).strip())
    blob = f"{serp_title} {snippet}".lower()
    if not any(len(a) >= 3 and a in blob for a in aliases):
        return False
    if "yahoo" in blob and not any(a in blob for a in aliases if "yahoo" not in a):
        return False
    if "helium" in blob and "sarvam" not in blob.lower() and "sarvam" in company.lower():
        return False
    return True


async def discover_people(company_name: str, domain: str | None) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    people: list[dict] = []
    key = (os.getenv("SERPAPI_API_KEY") or "").strip()

    if key:
        q = f'site:linkedin.com/in "{company_name}" {PEOPLE_QUERY}'
        url = "https://serpapi.com/search.json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, params={"engine": "google", "q": q, "num": 20, "api_key": key})
            if res.status_code == 200:
                for item in res.json().get("organic_results", []):
                    link = item.get("link", "")
                    if "linkedin.com/in" not in link:
                        continue
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    if not _person_works_at_company(title, snippet, company_name):
                        continue
                    name = title.split("-")[0].split("|")[0].strip()
                    if len(name) < 3:
                        continue
                    people.append({
                        "name": name,
                        "title": snippet[:80] if snippet else "Professional",
                        "linkedinUrl": link.split("?")[0],
                        "email": None,
                        "phone": None,
                        "emailConfidence": "not_found",
                        "phoneConfidence": "not_found",
                        "source": f"SerpAPI · {company_name}",
                    })
                    if len(people) >= 10:
                        break
    else:
        warnings.append("Add SERPAPI_API_KEY for LinkedIn people search.")

    if len(people) < 5 and domain:
        try:
            raw = await llm_json_completion(
                'Extract up to 10 senior people for cold outreach at this company. JSON: {"people":[{"name","title","email","phone"}]}. No juniors.',
                {"company": company_name, "domain": domain},
            )
            for p in raw.get("people", [])[:10]:
                people.append({
                    "name": p.get("name", ""),
                    "title": p.get("title", ""),
                    "linkedinUrl": f"https://www.linkedin.com/search/results/people/?keywords={p.get('name','')}+{company_name}",
                    "email": p.get("email"),
                    "phone": p.get("phone"),
                    "emailConfidence": "likely" if p.get("email") else "not_found",
                    "phoneConfidence": "likely" if p.get("phone") else "not_found",
                    "source": "Python LLM · page",
                })
        except Exception:
            pass

    warnings.append("People: current employees / leaders only (no SDE1).")
    return people[:10], warnings


async def run_company_search(company_name: str, target_roles: list[str]) -> dict:
    warnings: list[str] = []
    company = await resolve_company(company_name)
    if not company.get("domain"):
        warnings.append("Could not verify company website.")

    jobs = []
    if company.get("careersUrl"):
        jobs = await fetch_jobs(company["careersUrl"], target_roles)
    else:
        warnings.append("Careers page not found.")

    people, pw = await discover_people(company["name"], company.get("domain"))
    warnings.extend(pw)

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "company": company,
        "people": people,
        "jobs": jobs,
        "warnings": list(dict.fromkeys(warnings)),
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
