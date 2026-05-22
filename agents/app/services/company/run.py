"""Company intelligence, people discovery, and jobs — Python agents."""

import json
import os
import re
import uuid
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import RUNS_DIR
from app.services.company.job_ats import enrich_jobs_with_ats
from app.services.company.job_detail import fetch_job_posting_text
from app.services.company.jobs import discover_careers_portal, fetch_jobs_deep, fetch_html
from app.services.company.contact_hints import contact_lookup_hints
from app.services.company.roles import (
    PEOPLE_PER_ROLE,
    ROLE_LINKEDIN_TITLES,
    ROLE_SENIOR_QUERY,
    seniority_score,
    title_matches_role,
)
from app.services.jd.run import run_jd_tailor
from app.services.resume.parser import load_resume

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


def _company_aliases(company: str) -> set[str]:
    base = company.lower().strip()
    aliases = {base}
    aliases.add(re.sub(r"\b(inc|llc|ltd|corp)\b\.?", "", base).strip())
    first = base.split()[0] if base else ""
    if len(first) >= 3:
        aliases.add(first)
    return {a for a in aliases if len(a) >= 3}


def _person_works_at_company(serp_title: str, snippet: str, company: str) -> bool:
    """Require company name in the LinkedIn result title (not snippet alone)."""
    aliases = _company_aliases(company)
    title_lower = serp_title.lower()
    if any(a in title_lower for a in aliases):
        return True
    # Allow snippet only if title also has a clear employer segment (Name - Role - Co)
    parts = [p.strip() for p in serp_title.split("-") if p.strip()]
    if len(parts) >= 3:
        employer = parts[-1].split("|")[0].strip().lower()
        if any(a in employer for a in aliases):
            return True
    return False


def _linkedin_job_title(serp_title: str, snippet: str) -> str:
    parts = [p.strip() for p in serp_title.split("-") if p.strip()]
    if len(parts) >= 2:
        role = parts[1].split("|")[0].strip()
        if role and "linkedin" not in role.lower():
            return role[:120]
    return snippet[:100] if snippet else "Professional"


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
    job_title = _linkedin_job_title(title, snippet)
    if not title_matches_role(job_title, matched_role):
        return None

    return {
        "name": name,
        "title": job_title,
        "linkedinUrl": link.split("?")[0],
        "email": None,
        "phone": None,
        "emailConfidence": "not_found",
        "phoneConfidence": "not_found",
        "source": f"SerpAPI · {company_name}",
        "matchedRole": matched_role,
        "seniorityRank": seniority_score(job_title),
    }


def _attach_contact_hints(person: dict, company_name: str, domain: str | None) -> dict:
    if not person.get("email"):
        person["contactHints"] = contact_lookup_hints(
            company_name, person.get("name", ""), domain
        )
    return person


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
            f"Add SERPAPI_API_KEY for LinkedIn search ({PEOPLE_PER_ROLE} senior people per role)."
        )
    else:
        async with httpx.AsyncClient(timeout=35.0) as client:
            for role in target_roles:
                titles = ROLE_LINKEDIN_TITLES.get(role, role)
                senior = ROLE_SENIOR_QUERY.get(role, "")
                title_clause = f"({titles})"
                if senior:
                    title_clause = f"({titles} OR {senior})"

                q = (
                    f'site:linkedin.com/in "{company_name}" '
                    f"{title_clause} "
                    '-intitle:"jobs" -intitle:"job"'
                )
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": q,
                        "num": 30,
                        "api_key": key,
                    },
                )
                if res.status_code != 200:
                    warnings.append(f"SerpAPI failed for role: {role}")
                    continue

                candidates: list[dict] = []
                for item in res.json().get("organic_results", []):
                    person = _parse_person(item, company_name, role)
                    if not person:
                        continue
                    link = person["linkedinUrl"]
                    if link in seen_links:
                        continue
                    candidates.append(person)

                candidates.sort(
                    key=lambda p: p.get("seniorityRank", 0),
                    reverse=True,
                )

                role_count = 0
                for person in candidates:
                    link = person["linkedinUrl"]
                    seen_links.add(link)
                    person.pop("seniorityRank", None)
                    _attach_contact_hints(person, company_name, domain)
                    people.append(person)
                    people_by_role[role].append(person)
                    role_count += 1
                    if role_count >= PEOPLE_PER_ROLE:
                        break

                if role_count == 0:
                    warnings.append(
                        f"No LinkedIn profiles matched {role} (or equivalent senior titles) at {company_name}. "
                        "Try a careers URL override or a different role."
                    )
                elif role_count < PEOPLE_PER_ROLE:
                    warnings.append(
                        f"Found {role_count}/{PEOPLE_PER_ROLE} matching senior profiles for {role}."
                    )

    total_expected = PEOPLE_PER_ROLE * len(target_roles)
    warnings.insert(
        0,
        "People are ranked by seniority (Director / Head / Principal / Lead first) "
        f"and filtered to {', '.join(target_roles)} or equivalent titles only.",
    )
    warnings.append(
        f"LinkedIn: up to {PEOPLE_PER_ROLE} people per selected role "
        f"({len(target_roles)} roles → target {total_expected} total). "
        "Email/phone rarely appear on LinkedIn — see contact hints on each profile."
    )
    return people, people_by_role, warnings


async def run_company_search(
    company_name: str,
    target_roles: list[str],
    resume_id: str | None = None,
    careers_url_override: str | None = None,
) -> dict:
    warnings: list[str] = []
    company = await resolve_company(company_name)

    careers_url = company.get("careersUrl")
    extra_pages: list[str] = []

    if careers_url_override:
        careers_url = careers_url_override.rstrip("/")
        company["careersUrl"] = careers_url
    elif company.get("domain") or company_name:
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
        warnings.append(
            "Could not auto-find a careers page for this company. "
            "Check the company name spelling, or add SERPAPI_API_KEY in apps/web/.env for better discovery."
        )

    people, people_by_role, pw = await discover_people_for_roles(
        company["name"], company.get("domain"), target_roles
    )
    warnings.extend(pw)

    resume_attached = False
    if resume_id:
        resume = load_resume(resume_id)
        if resume:
            resume_attached = True
            enrich_jobs_with_ats(jobs, resume["parsedFacts"])
            warnings.append(
                "ATS % on each job is a preview (title + snippet). "
                "Use Tailor to fetch the full posting and edit your resume."
            )
        else:
            warnings.append("Resume ID invalid — re-upload on home for ATS and tailoring.")
    else:
        warnings.append(
            "Upload a resume on home to see ATS scores and tailor for each opening."
        )

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "company": company,
        "people": people,
        "peopleByRole": people_by_role,
        "jobs": jobs,
        "jobsByRole": jobs_by_role,
        "peoplePerRole": PEOPLE_PER_ROLE,
        "resumeAttached": resume_attached,
        "warnings": list(dict.fromkeys(warnings)),
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


async def tailor_resume_for_job(
    resume_id: str,
    job_url: str,
    job_title: str,
    snippet: str | None = None,
) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found. Upload on home first.")

    jd_text = await fetch_job_posting_text(job_url, job_title, snippet)
    if len(jd_text.strip()) < 80:
        raise ValueError(
            "Could not load enough job text from the posting. Open the link and use JD path with pasted text."
        )

    result = await run_jd_tailor(resume_id, jd_text)
    result["sourceJobUrl"] = job_url
    result["sourceJobTitle"] = job_title
    return result
