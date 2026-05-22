"""Company intelligence, people discovery, and jobs — Python agents."""

import json
import os
import re
import uuid
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import RUNS_DIR
from app.services.company.jobs import discover_careers_portal, fetch_jobs_deep, fetch_html
from app.services.company.roles import PEOPLE_PER_ROLE, ROLE_LINKEDIN_TITLES
from app.services.llm.client import llm_json_completion

USER_AGENT = "JobSearchCopilot/1.0 (local recruiter tool)"


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
        html = await fetch_html(host)
        if not html:
            continue
        domain = urlparse(host).hostname
        careers_url, _ = await discover_careers_portal(trimmed, domain)
        if careers_url:
            break
        if domain:
            break

    return {"name": trimmed, "domain": domain, "careersUrl": careers_url}


def _person_works_at_company(serp_title: str, snippet: str, company: str) -> bool:
    aliases = {company.lower().strip()}
    aliases.add(re.sub(r"\b(inc|llc|ltd|corp)\b\.?", "", company.lower()).strip())
    blob = f"{serp_title} {snippet}".lower()
    if not any(len(a) >= 3 and a in blob for a in aliases):
        return False
    return True


def _parse_person(item: dict, company_name: str, matched_role: str) -> dict | None:
    link = item.get("link", "")
    if "linkedin.com/in" not in link:
        return None
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    if not _person_works_at_company(title, snippet, company_name):
        return None
    name = title.split("-")[0].split("|")[0].strip()
    if len(name) < 3:
        return None
    return {
        "name": name,
        "title": snippet[:100] if snippet else "Professional",
        "linkedinUrl": link.split("?")[0],
        "email": None,
        "phone": None,
        "emailConfidence": "not_found",
        "phoneConfidence": "not_found",
        "source": f"SerpAPI · {company_name}",
        "matchedRole": matched_role,
    }


async def discover_people_for_roles(
    company_name: str,
    domain: str | None,
    target_roles: list[str],
) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
    warnings: list[str] = []
    people: list[dict] = []
    people_by_role: dict[str, list[dict]] = {r: [] for r in target_roles}
    seen_links: set[str] = set()
    key = (os.getenv("SERPAPI_API_KEY") or "").strip()

    if not key:
        warnings.append(
            f"Add SERPAPI_API_KEY for LinkedIn search ({PEOPLE_PER_ROLE} people per selected role)."
        )
    else:
        async with httpx.AsyncClient(timeout=35.0) as client:
            for role in target_roles:
                titles = ROLE_LINKEDIN_TITLES.get(role, role)
                q = (
                    f'site:linkedin.com/in "{company_name}" '
                    f"({titles}) "
                    '-intitle:"jobs" -intitle:"job"'
                )
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": q,
                        "num": max(PEOPLE_PER_ROLE + 5, 15),
                        "api_key": key,
                    },
                )
                if res.status_code != 200:
                    warnings.append(f"SerpAPI failed for role: {role}")
                    continue

                role_count = 0
                for item in res.json().get("organic_results", []):
                    person = _parse_person(item, company_name, role)
                    if not person:
                        continue
                    link = person["linkedinUrl"]
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    people.append(person)
                    people_by_role[role].append(person)
                    role_count += 1
                    if role_count >= PEOPLE_PER_ROLE:
                        break

                if role_count < PEOPLE_PER_ROLE:
                    warnings.append(
                        f"Only {role_count}/{PEOPLE_PER_ROLE} LinkedIn profiles for {role}."
                    )

    total_expected = PEOPLE_PER_ROLE * len(target_roles)
    if len(people) < total_expected // 2 and domain:
        try:
            raw = await llm_json_completion(
                "Extract senior people at this company for outreach. JSON: "
                '{"people":[{"name","title","email","phone","roleHint"}]}. No interns.',
                {"company": company_name, "domain": domain, "roles": target_roles},
            )
            for p in raw.get("people", [])[:15]:
                link = f"https://www.linkedin.com/search/results/people/?keywords={p.get('name','')}+{company_name}"
                if link in seen_links:
                    continue
                seen_links.add(link)
                hint = p.get("roleHint") or target_roles[0]
                person = {
                    "name": p.get("name", ""),
                    "title": p.get("title", ""),
                    "linkedinUrl": link,
                    "email": p.get("email"),
                    "phone": p.get("phone"),
                    "emailConfidence": "likely" if p.get("email") else "not_found",
                    "phoneConfidence": "likely" if p.get("phone") else "not_found",
                    "source": "LLM fallback",
                    "matchedRole": hint if hint in target_roles else target_roles[0],
                }
                people.append(person)
                if hint in people_by_role and len(people_by_role[hint]) < PEOPLE_PER_ROLE:
                    people_by_role[hint].append(person)
        except Exception:
            pass

    warnings.append(
        f"LinkedIn: up to {PEOPLE_PER_ROLE} people per selected role "
        f"({len(target_roles)} roles → target {total_expected} total)."
    )
    return people, people_by_role, warnings


async def run_company_search(company_name: str, target_roles: list[str]) -> dict:
    warnings: list[str] = []
    company = await resolve_company(company_name)

    careers_url = company.get("careersUrl")
    extra_pages: list[str] = []
    if company.get("domain") or company_name:
        found, extra = await discover_careers_portal(
            company["name"], company.get("domain")
        )
        if found:
            careers_url = found
            company["careersUrl"] = found
        extra_pages = extra

    jobs: list[dict] = []
    jobs_by_role: dict[str, list[dict]] = {r: [] for r in target_roles}
    if careers_url:
        jobs, jobs_by_role, jw = await fetch_jobs_deep(
            careers_url, extra_pages, target_roles, company["name"], company.get("domain")
        )
        warnings.extend(jw)
    else:
        warnings.append("Careers portal not found — job list may be empty.")

    people, people_by_role, pw = await discover_people_for_roles(
        company["name"], company.get("domain"), target_roles
    )
    warnings.extend(pw)

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "company": company,
        "people": people,
        "peopleByRole": people_by_role,
        "jobs": jobs,
        "jobsByRole": jobs_by_role,
        "peoplePerRole": PEOPLE_PER_ROLE,
        "warnings": list(dict.fromkeys(warnings)),
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
