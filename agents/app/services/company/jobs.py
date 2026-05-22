"""Deep careers-portal job discovery — company-scoped only."""

import json
import os
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.company.company_match import (
    company_tokens,
    is_valid_job_title,
    job_url_belongs_to_company,
)
from app.services.company.roles import ROLE_PATTERNS

USER_AGENT = "JobSearchCopilot/1.0 (local recruiter tool)"
ATS_HOST_HINTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workday.com", "myworkdayjobs.com")


async def fetch_html(url: str, timeout: float = 18.0) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            res = await client.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json"},
            )
            if res.status_code >= 400:
                return None
            ct = res.headers.get("content-type", "")
            if "html" in ct or "json" in ct or not ct:
                return res.text
            return None
    except Exception:
        return None


def _score_title(title: str, roles: list[str]) -> tuple[int, str | None]:
    best = 0
    matched: str | None = None
    for role in roles:
        pat = ROLE_PATTERNS.get(role)
        if pat and pat.search(title):
            if best < 10:
                best = 10
                matched = role
    return best, matched


def _extract_jobs_from_html(
    html: str,
    base_url: str,
    roles: list[str],
    company_name: str,
    domain: str | None,
    careers_url: str | None,
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    jobs: list[dict] = []

    def maybe_add(title: str, job_url: str, snippet: str | None) -> None:
        if not is_valid_job_title(title):
            return
        url = urljoin(base_url, job_url)
        if url in seen:
            return
        if not job_url_belongs_to_company(url, company_name, domain, careers_url):
            return
        score, role = _score_title(title, roles)
        if score < 8:
            return
        seen.add(url)
        jobs.append({
            "title": title.strip(),
            "url": url,
            "location": None,
            "snippet": snippet,
            "matchScore": score,
            "matchedRole": role,
        })

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict) or item.get("@type") != "JobPosting":
                continue
            title = str(item.get("title") or "")
            job_url = str(item.get("url") or base_url)
            loc = item.get("jobLocation")
            location = loc.get("name") if isinstance(loc, dict) else None
            desc = (item.get("description") or "")[:200] or None
            if not job_url_belongs_to_company(
                urljoin(base_url, job_url), company_name, domain, careers_url
            ):
                continue
            score, role = _score_title(title, roles)
            if score < 8:
                continue
            u = urljoin(base_url, job_url)
            if u in seen:
                continue
            seen.add(u)
            jobs.append({
                "title": title.strip(),
                "url": u,
                "location": location,
                "snippet": desc,
                "matchScore": score,
                "matchedRole": role,
            })

    for a in soup.find_all("a", href=True):
        title = re.sub(r"\s+", " ", a.get_text()).strip()
        href = a["href"]
        parent = a.find_parent(["li", "div", "article"])
        snippet = parent.get_text(" ", strip=True)[:300] if parent else None
        maybe_add(title, href, snippet)

    return jobs


def _careers_candidate_urls(domain: str | None, company_name: str) -> list[str]:
    slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
    hosts: list[str] = []
    if domain:
        d = domain.replace("www.", "")
        hosts.extend([f"https://{d}", f"https://www.{d}"])
    if slug:
        hosts.extend([
            f"https://www.{slug}.com",
            f"https://{slug}.com",
            f"https://www.{slug}.io",
            f"https://{slug}.ai",
        ])
    paths = ["/careers", "/jobs", "/join-us", "/company/careers", "/about/careers", "/work-with-us"]
    urls: list[str] = []
    for h in dict.fromkeys(hosts):
        for p in paths:
            urls.append(urljoin(h, p))
    return urls


def _page_is_company_site(url: str, company_name: str, domain: str | None) -> bool:
    return job_url_belongs_to_company(url, company_name, domain, url)


def _pick_careers_from_serp_results(
    results: list[dict],
    company_name: str,
    domain: str | None,
) -> str | None:
    for item in results:
        link = (item.get("link") or "").strip()
        if not link:
            continue
        low = link.lower()
        if any(h in low for h in ATS_HOST_HINTS):
            return link.split("?")[0]
        if job_url_belongs_to_company(link, company_name, domain, None):
            if any(k in low for k in ("/career", "/job", "/opening", "/position", "/join")):
                return link.split("?")[0]
    return None


async def _discover_careers_via_serpapi(
    company_name: str, domain: str | None
) -> tuple[str | None, list[str]]:
    """Find careers / ATS board via Google when crawling common paths fails."""
    key = (os.getenv("SERPAPI_API_KEY") or "").strip()
    if not key:
        return None, []

    slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
    queries: list[str] = []
    if domain:
        d = domain.replace("www.", "")
        queries.append(f'site:{d} (careers OR jobs OR openings)')
    queries.extend([
        f'"{company_name}" careers jobs',
        f'site:boards.greenhouse.io "{company_name}" OR site:boards.greenhouse.io/{slug}',
        f'site:jobs.lever.co "{company_name}" OR site:jobs.lever.co/{slug}',
        f'site:jobs.ashbyhq.com "{company_name}"',
    ])

    try:
        async with httpx.AsyncClient(timeout=22.0) as client:
            for q in queries[:4]:
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={"engine": "google", "q": q, "num": 10, "api_key": key},
                )
                if res.status_code != 200:
                    continue
                found = _pick_careers_from_serp_results(
                    res.json().get("organic_results", []),
                    company_name,
                    domain,
                )
                if found:
                    return found, []
    except Exception:
        pass
    return None, []


async def discover_careers_portal(
    company_name: str, domain: str | None
) -> tuple[str | None, list[str]]:
    careers_url: str | None = None
    extra_pages: list[str] = []
    tokens = company_tokens(company_name, domain)

    for url in _careers_candidate_urls(domain, company_name):
        html = await fetch_html(url)
        if not html:
            continue
        low = html.lower()
        if not ("job" in low or "career" in low or "opening" in low or "position" in low):
            continue
        if not _page_is_company_site(url, company_name, domain):
            continue
        careers_url = url
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            full = urljoin(url, a["href"])
            if not job_url_belongs_to_company(full, company_name, domain, careers_url):
                if not any(ats in full for ats in ATS_HOST_HINTS):
                    continue
                if not any(len(t) >= 3 and t in full.lower() for t in tokens):
                    continue
            if full not in extra_pages and full != url:
                extra_pages.append(full)
        break

    if not careers_url and domain:
        for host in (f"https://{domain.replace('www.', '')}", f"https://www.{domain.replace('www.', '')}"):
            html = await fetch_html(host)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                t = (a.get_text() or "").lower()
                if "career" not in t and "job" not in t:
                    continue
                full = urljoin(host, a["href"])
                if job_url_belongs_to_company(full, company_name, domain, None):
                    careers_url = full
                    break
            if careers_url:
                break

    if not careers_url:
        careers_url, extra_pages = await _discover_careers_via_serpapi(company_name, domain)

    return careers_url, list(dict.fromkeys(extra_pages))[:15]


async def fetch_jobs_deep(
    careers_url: str,
    extra_pages: list[str],
    roles: list[str],
    company_name: str,
    domain: str | None,
) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
    warnings: list[str] = []
    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    pages = [careers_url] + [
        p for p in extra_pages
        if job_url_belongs_to_company(p, company_name, domain, careers_url)
    ]

    for page in pages:
        html = await fetch_html(page, timeout=22.0)
        if not html:
            continue
        for job in _extract_jobs_from_html(
            html, page, roles, company_name, domain, careers_url
        ):
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)

    key = (__import__("os").getenv("SERPAPI_API_KEY") or "").strip()
    if key and len(all_jobs) < 8:
        tokens = company_tokens(company_name, domain)
        slug = next((t for t in tokens if len(t) >= 4), "")
        role_hint = " OR ".join(f'"{r}"' for r in roles[:4])
        queries: list[str] = []
        if domain:
            queries.append(f'site:{domain.replace("www.", "")} ({role_hint}) (careers OR jobs)')
        if slug:
            queries.append(
                f'site:boards.greenhouse.io/{slug} OR site:jobs.lever.co/{slug} ({role_hint})'
            )
        queries.append(f'"{company_name}" careers openings ({role_hint})')

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                for q in queries[:2]:
                    res = await client.get(
                        "https://serpapi.com/search.json",
                        params={"engine": "google", "q": q, "num": 12, "api_key": key},
                    )
                    if res.status_code != 200:
                        continue
                    for item in res.json().get("organic_results", []):
                        link = item.get("link", "")
                        title = item.get("title", "")
                        if not link or not is_valid_job_title(title):
                            continue
                        if not job_url_belongs_to_company(
                            link, company_name, domain, careers_url
                        ):
                            continue
                        score, role = _score_title(title, roles)
                        if score < 8:
                            continue
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)
                        all_jobs.append({
                            "title": title,
                            "url": link,
                            "location": None,
                            "snippet": item.get("snippet"),
                            "matchScore": score,
                            "matchedRole": role,
                        })
                    if len(all_jobs) >= 8:
                        break
        except Exception:
            warnings.append("SerpAPI job boost failed.")

    all_jobs.sort(key=lambda j: j["matchScore"], reverse=True)

    by_role: dict[str, list[dict]] = {r: [] for r in roles}
    for job in all_jobs:
        role = job.get("matchedRole")
        if role and role in by_role and len(by_role[role]) < 15:
            by_role[role].append(job)
        else:
            for r in roles:
                pat = ROLE_PATTERNS.get(r)
                if pat and pat.search(job["title"]) and len(by_role[r]) < 15:
                    by_role[r].append(job)
                    break

    if len(all_jobs) == 0:
        warnings.append(
            "No matching jobs on this company's careers site for the roles you selected."
        )
    else:
        warnings.append(
            f"Found {len(all_jobs)} job(s) scoped to {company_name} only (random job boards filtered out)."
        )

    return all_jobs[:40], by_role, warnings
