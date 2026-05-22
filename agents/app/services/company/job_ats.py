"""ATS preview for job listings vs uploaded resume."""

from app.services.company.job_detail import job_text_for_ats_preview
from app.services.jd.run import compute_ats_breakdown, extract_jd_keywords


def enrich_jobs_with_ats(jobs: list[dict], parsed_facts: dict) -> None:
    claims = parsed_facts.get("allowedClaims") or []
    for job in jobs:
        jd_text = job_text_for_ats_preview(job)
        if len(jd_text) < 20:
            job["atsScorePercent"] = None
            job["atsBreakdown"] = None
            continue
        keywords = extract_jd_keywords(jd_text)
        breakdown = compute_ats_breakdown(keywords, claims, [])
        job["atsScorePercent"] = breakdown["scorePercent"]
        job["atsBreakdown"] = breakdown
