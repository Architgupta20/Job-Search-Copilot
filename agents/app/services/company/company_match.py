"""Verify jobs and URLs belong to the target company."""

import re
from urllib.parse import urlparse

# Generic job boards / social — not company-specific listings
BLOCKED_JOB_HOSTS = (
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "ziprecruiter.com",
    "simplyhired.com",
    "talent.com",
    "dice.com",
    "wellfound.com",
    "angellist.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "youtube.com",
    "google.com",
    "wikipedia.org",
    "github.com",
    "medium.com",
)

JOB_PATH_HINTS = (
    "/job",
    "/jobs",
    "/career",
    "/position",
    "/opening",
    "/role",
    "/requisition",
    "/opportunit",
    "/apply",
    "/posting",
)

NAV_TITLE_BLOCKLIST = re.compile(
    r"^(home|about|contact|privacy|terms|cookie|login|sign in|apply now|learn more|"
    r"read more|see all|view all|back to|our team|blog|news|press|faq|help|support)$",
    re.I,
)

ATS_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com", "workday.com")


def company_tokens(company_name: str, domain: str | None) -> set[str]:
    tokens: set[str] = set()
    slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
    if len(slug) >= 3:
        tokens.add(slug)
    words = re.findall(r"[a-z0-9]{3,}", company_name.lower())
    for w in words:
        if w not in {"inc", "llc", "ltd", "corp", "the", "and"}:
            tokens.add(w)
    if domain:
        host = domain.lower().replace("www.", "")
        root = host.split(".")[0]
        if len(root) >= 3:
            tokens.add(root)
        tokens.add(host.replace(".", ""))
    return tokens


def _host_root(hostname: str) -> str:
    h = (hostname or "").lower().replace("www.", "")
    parts = h.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return h


def job_url_belongs_to_company(
    url: str,
    company_name: str,
    domain: str | None,
    careers_url: str | None,
) -> bool:
    if not url or not url.startswith("http"):
        return False

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()
    full = url.lower()

    if any(blocked in host for blocked in BLOCKED_JOB_HOSTS):
        return False

    tokens = company_tokens(company_name, domain)

    # Company's own domain (and subdomains)
    if domain:
        company_root = _host_root(domain.replace("www.", ""))
        if _host_root(host) == company_root or host.endswith("." + company_root):
            return _looks_like_job_link(path, full)

    # Careers page is on same site — allow same host as careers_url
    if careers_url:
        ch = (urlparse(careers_url).hostname or "").lower()
        if ch and (host == ch or host.endswith(ch.replace("www.", ""))):
            return _looks_like_job_link(path, full)

    # ATS boards must include company token in URL path/host
    if any(ats in host for ats in ATS_HOSTS):
        blob = f"{host}{path}"
        if any(len(t) >= 3 and t in blob for t in tokens):
            return True
        return False

    # jobs.{company}.com etc.
    if any(len(t) >= 3 and t in host for t in tokens):
        return _looks_like_job_link(path, full)

    return False


def _looks_like_job_link(path: str, full_url: str) -> bool:
    if any(hint in path for hint in JOB_PATH_HINTS):
        return True
    if any(ats in full_url for ats in ATS_HOSTS):
        return True
    # Greenhouse/Lever embed links on company site
    if "greenhouse" in full_url or "lever.co" in full_url:
        return True
    return False


def is_valid_job_title(title: str) -> bool:
    t = title.strip()
    if len(t) < 8 or len(t) > 120:
        return False
    if NAV_TITLE_BLOCKLIST.match(t):
        return False
    if t.count(" ") > 18:
        return False
    return True
