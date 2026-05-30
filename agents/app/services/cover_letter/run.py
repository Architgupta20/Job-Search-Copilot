"""Fact-only cover letter drafts from resume + optional JD."""

from __future__ import annotations

import re
import uuid

from app.config import JD_RUNS_DIR
from app.services.company.cold_email import (
    _company_key,
    _contribution_paragraph,
    _first_name,
    _pick_experience_bullets,
    _resolve_hook,
    _skills_summary,
)
from app.services.company.company_research import research_company_angle
from app.services.jd.run import extract_jd_keywords
from app.services.resume.parser import load_resume


def _jd_keywords_in_resume(jd_keywords: list[str], claims: list[str]) -> list[str]:
    blob = " ".join(claims).lower()
    matched: list[str] = []
    for kw in jd_keywords:
        if kw in blob and kw not in matched:
            matched.append(kw)
    return matched[:12]


def _pick_bullets_for_jd(claims: list[str], jd_keywords: list[str], max_items: int = 3) -> list[str]:
    if not claims:
        return []
    if not jd_keywords:
        return _pick_experience_bullets(claims, max_items)

    scored: list[tuple[int, str]] = []
    for c in claims:
        line = re.sub(r"\s+", " ", (c or "").strip())
        if len(line) < 20:
            continue
        low = line.lower()
        score = sum(1 for kw in jd_keywords if kw in low)
        scored.append((score, line))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [line for score, line in scored if score > 0][:max_items]
    if len(picked) < max_items:
        for line in _pick_experience_bullets(claims, max_items):
            if line not in picked:
                picked.append(line)
            if len(picked) >= max_items:
                break
    return picked[:max_items]


def _compose_cover_letter(
    *,
    candidate_name: str,
    candidate_email: str | None,
    company_name: str,
    role_title: str,
    hook: str,
    bullets: list[str],
    skills_summary: str,
    contribution: str,
    jd_keywords_matched: list[str],
) -> str:
    bullet_block = "\n".join(f"• {b}" for b in bullets)
    kw_line = (
        f"From the job description, my background aligns with: {', '.join(jd_keywords_matched)}."
        if jd_keywords_matched
        else ""
    )

    sig = candidate_name
    if candidate_email:
        sig = f"{candidate_name}\n{candidate_email}"

    parts = [
        f"Dear Hiring Manager,",
        "",
        (
            f"I am writing to apply for the {role_title} role at {company_name}. "
            f"{hook.rstrip('.')}."
        ),
        "",
        "Highlights from my experience (from my resume only):",
        bullet_block,
        "",
        f"Relevant strengths: {skills_summary}.",
        contribution,
    ]
    if kw_line:
        parts.extend(["", kw_line])
    parts.extend(
        [
            "",
            (
                f"I would welcome the opportunity to discuss how I can contribute to "
                f"{company_name}'s team. Thank you for your time and consideration."
            ),
            "",
            "Sincerely,",
            sig,
        ]
    )
    return "\n".join(parts).strip()


async def run_cover_letter(
    resume_id: str,
    company_name: str,
    role_title: str,
    jd_text: str | None = None,
    company_domain: str | None = None,
) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found. Upload again from home.")

    facts = resume["parsedFacts"]
    contact = facts.get("contact") or {}
    candidate_name = contact.get("name") or "[Your name]"
    candidate_email = contact.get("email")
    claims = [c for c in (facts.get("allowedClaims") or []) if isinstance(c, str)]

    company = company_name.strip()
    role = role_title.strip()
    jd_clean = (jd_text or "").strip()
    jd_keywords = extract_jd_keywords(jd_clean) if len(jd_clean) >= 80 else []
    jd_matched = _jd_keywords_in_resume(jd_keywords, claims) if jd_keywords else []

    research = await research_company_angle(company, company_domain)
    ckey = _company_key(company, company_domain)
    hook = await _resolve_hook(company, company_domain, research.get("companyAngle", ""))

    bullets = _pick_bullets_for_jd(claims, jd_keywords, 3)
    skills = _skills_summary(claims)
    contribution = _contribution_paragraph(company, ckey, role, claims)

    body = _compose_cover_letter(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        company_name=company,
        role_title=role,
        hook=hook,
        bullets=bullets,
        skills_summary=skills,
        contribution=contribution,
        jd_keywords_matched=jd_matched,
    )

    warnings = [
        "Cover letter uses only facts from your uploaded resume — no invented tools, employers, or metrics.",
        "Edit the draft in Word before sending.",
    ]
    if jd_keywords and not jd_matched:
        warnings.append(
            "Few JD keywords matched your resume text — letter stays truthful; consider JD tailor for bullet edits."
        )

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "companyName": company,
        "roleTitle": role,
        "body": body,
        "jdKeywordsMatched": jd_matched,
        "jdKeywordsMissing": [k for k in jd_keywords if k not in jd_matched][:20],
        "resumeBulletsUsed": bullets,
        "warnings": warnings,
    }

    JD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    import json

    (JD_RUNS_DIR / f"cover-{run_id}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result
