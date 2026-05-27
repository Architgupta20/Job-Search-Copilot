"""Company intelligence, people discovery, and jobs — Python agents."""

import json
import os
import re
import uuid
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import RUNS_DIR
from app.light_mode import (
    is_light_mode,
    people_per_role,
    serp_page_starts,
    serp_query_limit,
    skip_careers_scrape,
    skip_company_host_probe,
)
from app.services.company.job_ats import enrich_jobs_with_ats
from app.services.company.job_detail import fetch_job_posting_text
from app.services.company.jobs import discover_careers_portal, fetch_jobs_deep, fetch_html
from app.services.company.contact_enrichment import enrich_people_contacts
from app.services.company.locations import (
    location_label,
    person_matches_location,
    query_location_terms,
    serpapi_location,
)
from app.services.company.roles import (
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
    if skip_company_host_probe():
        slug = _slugify(trimmed)
        domain = f"{slug}.com" if slug else None
        return {"name": trimmed, "domain": domain, "careersUrl": None}

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
    """
    Google LinkedIn hits often use title 'Name | LinkedIn' and put employer in the snippet.
    Accept company in title, employer segment, or snippet (for linkedin.com/in URLs).
    """
    aliases = _company_aliases(company)
    title_lower = serp_title.lower()
    snippet_lower = (snippet or "").lower()
    blob = f"{title_lower} {snippet_lower}"

    if any(len(a) >= 3 and a in title_lower for a in aliases):
        return True

    parts = [p.strip() for p in serp_title.split("-") if p.strip()]
    if len(parts) >= 3:
        employer = parts[-1].split("|")[0].strip().lower()
        if any(a in employer for a in aliases):
            return True

    # Typical Google format: company only in snippet ("… at Razorpay · …")
    if any(len(a) >= 3 and a in blob for a in aliases):
        if "linkedin" in title_lower or "linkedin.com/in" in blob:
            return True
    return False


def _is_current_employee(snippet: str, serp_title: str, company_name: str) -> bool:
    """Drop ex-employees; keep profiles that look like current roles at the company."""
    blob = f"{snippet} {serp_title}"
    low = blob.lower()
    aliases = _company_aliases(company_name)

    if not any(len(a) >= 3 and a in low for a in aliases):
        return False

    if re.search(r"\b(present|currently|current role|–\s*present|to present)\b", low):
        return True

    for alias in aliases:
        if len(alias) < 3:
            continue
        for m in re.finditer(re.escape(alias), low):
            window = low[max(0, m.start() - 45) : m.end() + 55]
            if re.search(
                r"former|ex-employee|ex employee|previously at|past:\s*|"
                r"used to work|until \d{4}|left in \d{4}",
                window,
            ):
                continue
            if re.search(rf"\bat\s+{re.escape(alias)}\b", window):
                before = low[max(0, m.start() - 35) : m.start()]
                if re.search(r"former|ex-|previously", before):
                    continue
                return True

    if re.search(r"\b(former|ex-|previously at|past employee)\b", low):
        return False

    return True


def _linkedin_job_title(serp_title: str, snippet: str) -> str:
    snip = snippet or ""
    at_match = re.search(
        r"(?:^|[.;]\s*)(?:In my role as\s+)?([^·|]{2,80}?)\s+at\s+",
        snip,
        re.I,
    )
    if at_match:
        title = at_match.group(1).strip()
        title = re.sub(
            r"^(in my role as|my role as|working as|as an?|as)\s+",
            "",
            title,
            flags=re.I,
        )
        if title and "linkedin" not in title.lower():
            return title[:120]

    parts = [p.strip() for p in serp_title.split("-") if p.strip()]
    if len(parts) >= 2:
        role = parts[1].split("|")[0].strip()
        if role and "linkedin" not in role.lower():
            return role[:120]
    return "Professional"


def _parse_person(item: dict, company_name: str, matched_role: str) -> dict | None:
    link = item.get("link", "")
    if "linkedin.com/in" not in link:
        return None
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    if not _person_works_at_company(title, snippet, company_name):
        return None
    if not _is_current_employee(snippet, title, company_name):
        return None
    name = title.split("-")[0].split("|")[0].strip()
    if len(name) < 3:
        return None
    job_title = _linkedin_job_title(title, snippet)
    role_blob = f"{job_title} {title} {snippet}"
    if not title_matches_role(role_blob, matched_role):
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


async def discover_people_for_roles(
    company_name: str,
    domain: str | None,
    target_roles: list[str],
    location_country: str | None = None,
    location_city: str | None = None,
) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
    warnings: list[str] = []
    people: list[dict] = []
    people_by_role: dict[str, list[dict]] = {r: [] for r in target_roles}
    seen_links: set[str] = set()
    key = (os.getenv("SERPAPI_API_KEY") or "").strip()
    loc_terms = query_location_terms(location_country, location_city)
    serp_loc = serpapi_location(location_country, location_city)
    loc_display = location_label(location_country, location_city)

    per_role = people_per_role()
    if not key:
        warnings.append(
            f"Add SERPAPI_API_KEY for LinkedIn search ({per_role} senior people per role)."
        )
    else:
        if is_light_mode():
            warnings.append(
                "Lite mode (JOB_COPILOT_LIGHT): max 3 people/role, 1 SerpAPI query/role. "
                "Use Outreach drafts for manual contacts."
            )
        async with httpx.AsyncClient(timeout=35.0) as client:
            for role in target_roles:
                titles = ROLE_LINKEDIN_TITLES.get(role, role)
                senior = ROLE_SENIOR_QUERY.get(role, "")
                title_clause = f"({titles})"
                if senior:
                    title_clause = f"({titles} OR {senior})"

                loc_suffix = f" {loc_terms}" if loc_terms else ""
                queries = [
                    f"site:linkedin.com/in {company_name} {role}{loc_suffix}",
                    f'site:linkedin.com/in "{company_name}" "{role}"{loc_suffix}',
                    (
                        f'site:linkedin.com/in "{company_name}" {title_clause}{loc_suffix} '
                        '-intitle:"jobs" -intitle:"job"'
                    ),
                ][: serp_query_limit()]

                candidates: list[dict] = []
                candidate_links: set[str] = set()

                for q in queries:
                    for start in serp_page_starts():
                        params: dict = {
                            "engine": "google",
                            "q": q,
                            "num": 10,
                            "start": start,
                            "api_key": key,
                        }
                        if serp_loc:
                            params["location"] = serp_loc
                        res = await client.get(
                            "https://serpapi.com/search.json",
                            params=params,
                        )
                        if res.status_code != 200:
                            if start == 0:
                                warnings.append(f"SerpAPI failed for role: {role}")
                            break

                        batch = res.json().get("organic_results", [])
                        if not batch:
                            break

                        for item in batch:
                            person = _parse_person(item, company_name, role)
                            if not person:
                                continue
                            if not person_matches_location(
                                snippet=item.get("snippet", ""),
                                serp_title=item.get("title", ""),
                                country=location_country,
                                city=location_city,
                            ):
                                continue
                            link = person["linkedinUrl"]
                            if link in candidate_links:
                                continue
                            candidate_links.add(link)
                            candidates.append(person)

                        if len(candidates) >= per_role + 8:
                            break
                    if len(candidates) >= per_role + 8:
                        break

                candidates.sort(
                    key=lambda p: p.get("seniorityRank", 0),
                    reverse=True,
                )

                role_count = 0
                for person in candidates:
                    link = person["linkedinUrl"]
                    seen_links.add(link)
                    person.pop("seniorityRank", None)
                    people.append(person)
                    people_by_role[role].append(person)
                    role_count += 1
                    if role_count >= per_role:
                        break

                if role_count == 0:
                    loc_hint = (
                        f" in {loc_display}" if loc_display else ""
                    )
                    warnings.append(
                        f"No LinkedIn profiles matched {role} (or equivalent senior titles) at "
                        f"{company_name}{loc_hint}. "
                        "Try another city, broader country only, or a different role."
                    )
                elif role_count < per_role:
                    warnings.append(
                        f"Found {role_count}/{per_role} matching senior profiles for {role}."
                    )

    total_expected = per_role * len(target_roles)
    loc_note = (
        f" Location filter: {loc_display}."
        if loc_display
        else " Location: worldwide (no country/city filter)."
    )
    warnings.insert(
        0,
        "People: current employees only (ex-employees filtered out), via Google-indexed LinkedIn — "
        "ranked senior-first for your role or equivalents."
        + loc_note,
    )
    if people and not is_light_mode():
        warnings.append(
            "Researching email/phone via Hunter.io + Google + company pages (30–90s)…"
        )
        await enrich_people_contacts(people, company_name, domain)
        people_by_role = {r: [] for r in target_roles}
        for p in people:
            mr = p.get("matchedRole")
            if mr in people_by_role:
                people_by_role[mr].append(p)
    elif people and is_light_mode():
        warnings.append(
            "Lite mode: skipped bulk email lookup. Use Find email (Hunter) on each contact in Outreach drafts."
        )

    warnings.append(
        f"LinkedIn: up to {per_role} people per selected role "
        f"({len(target_roles)} roles → target {total_expected} total). "
        "Add HUNTER_API_KEY in apps/web/.env for best email discovery."
    )
    return people, people_by_role, warnings


async def run_company_search(
    company_name: str,
    target_roles: list[str],
    resume_id: str | None = None,
    careers_url_override: str | None = None,
    location_country: str | None = None,
    location_city: str | None = None,
) -> dict:
    warnings: list[str] = []
    company = await resolve_company(company_name)

    careers_url = company.get("careersUrl")
    extra_pages: list[str] = []

    if careers_url_override:
        careers_url = careers_url_override.rstrip("/")
        company["careersUrl"] = careers_url
    elif not skip_careers_scrape() and (company.get("domain") or company_name):
        found, extra = await discover_careers_portal(
            company["name"], company.get("domain")
        )
        if found:
            careers_url = found
            company["careersUrl"] = found
        extra_pages = extra

    jobs: list[dict] = []
    jobs_by_role: dict[str, list[dict]] = {r: [] for r in target_roles}
    if skip_careers_scrape():
        warnings.append(
            "Lite mode: careers job scrape skipped (saves CPU). Use Outreach drafts + JD tailor, "
            "or run without JOB_COPILOT_LIGHT for full company search."
        )
    elif careers_url:
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
        company["name"],
        company.get("domain"),
        target_roles,
        location_country=location_country,
        location_city=location_city,
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
        "searchLocation": location_label(location_country, location_city),
        "people": people,
        "peopleByRole": people_by_role,
        "jobs": jobs,
        "jobsByRole": jobs_by_role,
        "peoplePerRole": people_per_role(),
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
