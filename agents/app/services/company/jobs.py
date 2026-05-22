"""Deep careers-portal job discovery."""

import json
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

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


def _extract_jobs_from_html(html: str, base_url: str, roles: list[str]) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    jobs: list[dict] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") not in ("JobPosting",):
                continue
            title = item.get("title") or ""
            job_url = item.get("url") or base_url
            score, role = _score_title(str(title), roles)
            if score < 8:
                continue
            url = urljoin(base_url, str(job_url))
            if url in seen:
                continue
            seen.add(url)
            jobs.append({
                "title": str(title).strip(),
                "url": url,
                "location": (item.get("jobLocation") or {}).get("name") if isinstance(item.get("jobLocation"), dict) else None,
                "snippet": (item.get("description") or "")[:200] or None,
                "matchScore": score,
                "matchedRole": role,
            })

    for a in soup.find_all("a", href=True):
        title = re.sub(r"\s+", " ", a.get_text()).strip()
        if len(title) < 6 or len(title) > 140:
            continue
        href = a["href"]
        if any(x in href.lower() for x in ("mailto:", "javascript:", "#", "linkedin.com")):
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        score, role = _score_title(title, roles)
        if score < 8:
            continue
        parent_text = ""
        parent = a.find_parent(["li", "div", "article"])
        if parent:
            parent_text = parent.get_text(" ", strip=True)[:300]
        seen.add(url)
        jobs.append({
            "title": title,
            "url": url,
            "location": None,
            "snippet": parent_text or None,
            "matchScore": score,
            "matchedRole": role,
        })

    return jobs


def _careers_candidate_urls(domain: str | None, company_name: str) -> list[str]:
    slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
    hosts: list[str] = []
    if domain:
        hosts.append(f"https://{domain}")
        hosts.append(f"https://www.{domain}")
    if slug:
        hosts.extend([
            f"https://www.{slug}.com",
            f"https://{slug}.com",
            f"https://www.{slug}.io",
            f"https://{slug}.ai",
        ])
    paths = [
        "/careers",
        "/jobs",
        "/join-us",
        "/company/careers",
        "/about/careers",
        "/work-with-us",
    ]
    urls: list[str] = []
    for h in dict.fromkeys(hosts):
        for p in paths:
            urls.append(urljoin(h, p))
    return urls


async def discover_careers_portal(company_name: str, domain: str | None) -> tuple[str | None, list[str]]:
    """Find careers URL and related ATS / job-board links."""
    warnings: list[str] = []
    careers_url: str | None = None
    extra_pages: list[str] = []

    for url in _careers_candidate_urls(domain, company_name):
        html = await fetch_html(url)
        if not html:
            continue
        low = html.lower()
        if "job" in low or "career" in low or "opening" in low:
            careers_url = url
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                full = urljoin(url, a["href"])
                text = (a.get_text() or "").lower()
                if any(h in full for h in ATS_HOST_HINTS):
                    extra_pages.append(full)
                if "greenhouse" in full or "lever.co" in full or "ashby" in full:
                    extra_pages.append(full)
                if ("view" in text or "opening" in text or "position" in text) and "job" in full.lower():
                    if full not in extra_pages and full != url:
                        extra_pages.append(full)
            break

    if not careers_url and domain:
        for host in (f"https://{domain}", f"https://www.{domain}"):
            html = await fetch_html(host)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                t = (a.get_text() or "").lower()
                if "career" in t or "job" in t:
                    careers_url = urljoin(host, a["href"])
                    break
            if careers_url:
                break

    if not careers_url:
        warnings.append("Could not find careers portal — try exact company website name.")

    return careers_url, list(dict.fromkeys(extra_pages))[:12]


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

    pages = [careers_url, *extra_pages]
    for page in pages:
        html = await fetch_html(page, timeout=22.0)
        if not html:
            continue
        for job in _extract_jobs_from_html(html, page, roles):
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)

    key = (__import__("os").getenv("SERPAPI_API_KEY") or "").strip()
    if key and len(all_jobs) < 5:
        q = f'{company_name} careers {" OR ".join(roles[:3])} site:greenhouse.io OR site:lever.co OR site:jobs'
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={"engine": "google", "q": q, "num": 15, "api_key": key},
                )
                if res.status_code == 200:
                    for item in res.json().get("organic_results", []):
                        link = item.get("link", "")
                        title = item.get("title", "")
                        if not link or len(title) < 6:
                            continue
                        score, role = _score_title(title, roles)
                        if score < 8 and not any(
                            h in link for h in ATS_HOST_HINTS
                        ):
                            continue
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)
                        all_jobs.append({
                            "title": title,
                            "url": link,
                            "location": None,
                            "snippet": item.get("snippet"),
                            "matchScore": max(score, 8),
                            "matchedRole": role,
                        })
        except Exception:
            warnings.append("SerpAPI job search failed.")

    all_jobs.sort(key=lambda j: j["matchScore"], reverse=True)

    by_role: dict[str, list[dict]] = {r: [] for r in roles}
    for job in all_jobs:
        role = job.get("matchedRole")
        if role and role in by_role:
            if len(by_role[role]) < 15:
                by_role[role].append(job)
        else:
            for r in roles:
                pat = ROLE_PATTERNS.get(r)
                if pat and pat.search(job["title"]):
                    if len(by_role[r]) < 15:
                        by_role[r].append(job)
                    break

    if len(all_jobs) == 0:
        warnings.append(
            "No jobs parsed from careers portal — open the careers link manually or try more role filters."
        )
    else:
        warnings.append(f"Scanned careers portal and {len(pages)} related page(s).")

    return all_jobs[:40], by_role, warnings
