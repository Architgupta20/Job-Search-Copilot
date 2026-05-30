"""Fact-only interview prep: 5 questions + STAR prompts from resume."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from app.config import JD_RUNS_DIR
from app.services.company.cold_email import _pick_experience_bullets, _skills_summary
from app.services.cover_letter.run import _pick_bullets_for_jd
from app.services.jd.run import extract_jd_keywords
from app.services.llm.client import interview_prep_llm
from app.services.resume.parser import load_resume

_METRIC_RE = re.compile(
    r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\+?\s*(?:users|customers|ms|sec|seconds|minutes|hours|days|weeks|months|years|x|fold|k|m|b)?\b",
    re.I,
)


def _extract_metrics(text: str) -> list[str]:
    found = _METRIC_RE.findall(text or "")
    out: list[str] = []
    for m in found:
        m = m.strip()
        if m and m not in out:
            out.append(m)
    return out[:4]


def _star_from_bullet(bullet: str) -> dict[str, str]:
    metrics = _extract_metrics(bullet)
    metric_hint = (
        f" Use these figures from your resume if asked: {', '.join(metrics)}."
        if metrics
        else " Only cite numbers that appear in the resume line above."
    )
    return {
        "situation": (
            f'Set the scene using only what is implied in this resume line: "{bullet}". '
            "Name the team, product, or business context if the bullet mentions it."
        ),
        "task": (
            "What specific problem, deliverable, or KPI were you personally responsible for?"
        ),
        "action": (
            "Walk through what you did step by step. Stick to tools, methods, and scope "
            "mentioned in the resume line — do not add frameworks or employers."
        ),
        "result": (
            "State the outcome with concrete impact."
            + metric_hint
            + " Do not invent new metrics."
        ),
        "tip": (
            "If you led vs. supported is unclear in the bullet, answer honestly. "
            "Interviewers prefer precision over inflated ownership."
        ),
    }


def _role_fit_star(
    company: str, role: str, bullets: list[str], skills: str
) -> dict[str, str]:
    anchor = bullets[0] if bullets else skills
    return {
        "situation": (
            f"You are interviewing for {role} at {company}. "
            f"Ground your motivation in real experience from your resume."
        ),
        "task": (
            f"Explain why {role} at {company} fits your background and what you want to learn next."
        ),
        "action": (
            "Connect 2–3 resume facts to the role. Example anchor: "
            f'"{anchor}". Mention skills that match: {skills}.'
        ),
        "result": (
            f"Close with what you would contribute in the first 90 days — tied to {company}'s "
            "needs, using only resume-backed strengths."
        ),
        "tip": (
            "Avoid generic praise. Tie each reason to a specific resume bullet or skill you actually have."
        ),
    }


def _fallback_questions(
    company: str,
    role: str,
    jd_keywords: list[str],
    bullets: list[str],
    skills: str,
) -> list[dict[str, Any]]:
    kw = jd_keywords[0] if jd_keywords else None
    kw_phrase = kw.replace("_", " ") if kw else "production systems from your background"

    specs: list[tuple[str, str, int | None]] = [
        (
            "role-fit",
            f"Why are you interested in the {role} role at {company}?",
            None,
        ),
        (
            "technical",
            f"Walk me through your hands-on experience with {kw_phrase}.",
            0,
        ),
        (
            "behavioral",
            "Tell me about a challenging project you owned or contributed to. What made it hard?",
            1 if len(bullets) > 1 else 0,
        ),
        (
            "behavioral",
            "Describe a time you worked cross-functionally. How did you align stakeholders?",
            2 if len(bullets) > 2 else 1 if len(bullets) > 1 else 0,
        ),
        (
            "behavioral",
            "Share an example where your work had measurable impact. How did you track success?",
            3 if len(bullets) > 3 else 2 if len(bullets) > 2 else 0,
        ),
    ]

    questions: list[dict[str, Any]] = []
    for i, (category, question, bullet_idx) in enumerate(specs, start=1):
        if category == "role-fit":
            anchor = bullets[0] if bullets else skills
            star = _role_fit_star(company, role, bullets, skills)
        else:
            idx = bullet_idx if bullet_idx is not None else 0
            anchor = bullets[idx] if bullets else skills
            star = _star_from_bullet(anchor)

        questions.append(
            {
                "id": i,
                "question": question,
                "category": category,
                "resumeAnchor": anchor,
                "starPrompt": star,
            }
        )
    return questions


def _anchor_allowed(anchor: str, allowed: list[str]) -> bool:
    a = re.sub(r"\s+", " ", (anchor or "").strip())
    if not a:
        return False
    for line in allowed:
        if a == line or a in line or line in a:
            return True
    return False


def _normalize_llm_questions(
    raw: list[Any],
    allowed_anchors: list[str],
    company: str,
    role: str,
    bullets: list[str],
    skills: str,
) -> list[dict[str, Any]] | None:
    if not isinstance(raw, list) or len(raw) < 5:
        return None

    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw[:5], start=1):
        if not isinstance(row, dict):
            return None
        question = str(row.get("question") or "").strip()
        category = str(row.get("category") or "behavioral").strip().lower()
        if category not in ("behavioral", "technical", "role-fit"):
            category = "behavioral"
        anchor = str(row.get("resumeAnchor") or "").strip()
        star = row.get("starPrompt")
        if not question or not isinstance(star, dict):
            return None
        if not _anchor_allowed(anchor, allowed_anchors):
            anchor = bullets[min(i - 1, len(bullets) - 1)] if bullets else skills
        star_norm = {
            k: str(star.get(k) or "").strip()
            for k in ("situation", "task", "action", "result", "tip")
        }
        if not all(star_norm.values()):
            star_norm = _star_from_bullet(anchor) if category != "role-fit" else _role_fit_star(
                company, role, bullets, skills
            )
        out.append(
            {
                "id": i,
                "question": question,
                "category": category,
                "resumeAnchor": anchor,
                "starPrompt": star_norm,
            }
        )
    return out


async def run_interview_prep(
    resume_id: str,
    company_name: str,
    role_title: str,
    jd_text: str | None = None,
) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found. Upload again from home.")

    facts = resume["parsedFacts"]
    claims = [c for c in (facts.get("allowedClaims") or []) if isinstance(c, str)]
    company = company_name.strip()
    role = role_title.strip()
    jd_clean = (jd_text or "").strip()
    jd_keywords = extract_jd_keywords(jd_clean) if len(jd_clean) >= 80 else []

    bullets = _pick_bullets_for_jd(claims, jd_keywords, 5)
    if len(bullets) < 5:
        for line in _pick_experience_bullets(claims, 5):
            if line not in bullets:
                bullets.append(line)
            if len(bullets) >= 5:
                break
    bullets = bullets[:5]
    skills = _skills_summary(claims)
    allowed_anchors = bullets + [skills]

    questions: list[dict[str, Any]] | None = None
    source = "template"
    try:
        llm_out = await interview_prep_llm(
            {
                "companyName": company,
                "roleTitle": role,
                "jdKeywords": jd_keywords[:15],
                "resumeAnchors": [{"id": i + 1, "text": b} for i, b in enumerate(bullets)],
                "skillsSummary": skills,
            }
        )
        questions = _normalize_llm_questions(
            llm_out.get("questions") or [],
            allowed_anchors,
            company,
            role,
            bullets,
            skills,
        )
        if questions:
            source = "llm"
    except Exception:
        questions = None

    if not questions:
        questions = _fallback_questions(company, role, jd_keywords, bullets, skills)

    warnings = [
        "Questions and STAR prompts use only facts from your uploaded resume — no invented employers, tools, or metrics.",
        "Practice aloud; edit prompts to match how you actually describe each bullet.",
    ]
    if jd_keywords and not any(kw in " ".join(claims).lower() for kw in jd_keywords[:5]):
        warnings.append(
            "Few JD keywords matched your resume — technical questions stay general; consider JD tailor for alignment."
        )

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "companyName": company,
        "roleTitle": role,
        "questions": questions,
        "resumeBulletsUsed": bullets,
        "jdKeywordsUsed": jd_keywords[:12],
        "source": source,
        "warnings": warnings,
    }

    JD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (JD_RUNS_DIR / f"interview-{run_id}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result
