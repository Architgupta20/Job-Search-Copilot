"""
Outreach drafts — structured, resume-backed (no weak full-message LLM).
"""

from __future__ import annotations

import os
import re

from app.services.company.company_research import research_company_angle
from app.services.llm.client import llm_json_completion
from app.services.resume.parser import load_resume

KNOWN_COMPANY_HOOKS: dict[str, str] = {
    "razorpay": (
        "Razorpay scaling payments and merchant data platforms is one of the strongest "
        "infrastructure bets in Indian fintech."
    ),
    "stripe": (
        "Stripe's developer-first payments stack is still one of the clearest product "
        "bets in global fintech."
    ),
    "databricks": (
        "Databricks pushing the lakehouse for enterprise AI is one of the most practical "
        "data-platform bets in the market."
    ),
    "anthropic": (
        "Anthropic's focus on capable, safety-minded frontier models is one of the most "
        "serious bets in applied AI research."
    ),
    "openai": (
        "OpenAI's pace on usable frontier models is one of the defining bets in applied AI "
        "right now."
    ),
    "concentrix": (
        "Concentrix building AI into customer experience and automation is one of the most "
        "practical applied AI bets in services."
    ),
}

# (company_key, role keyword in target role) → how candidate could help
CONTRIBUTION_BY_ROLE: dict[tuple[str, str], str] = {
    (
        "razorpay",
        "product",
    ): (
        "At Razorpay, I could contribute by shaping merchant- and customer-facing journeys, "
        "running disciplined experiments on adoption and conversion, and partnering with "
        "engineering and data teams to ship AI-assisted product capabilities—without losing "
        "reliability on core payments."
    ),
    (
        "razorpay",
        "data",
    ): (
        "At Razorpay, I could contribute by building trustworthy data pipelines and models "
        "for payments and merchant analytics, improving decision quality for product and "
        "risk teams, and applying GenAI/RAG where it speeds operations without compromising "
        "accuracy."
    ),
    (
        "razorpay",
        "engineer",
    ): (
        "At Razorpay, I could contribute by shipping reliable, scalable services for payments "
        "and merchant platforms, improving observability and delivery practices, and applying "
        "ML/GenAI where it clearly improves merchant or customer outcomes."
    ),
}

HOOK_LLM_SYSTEM = """Rewrite into ONE natural English sentence for a job seeker's outreach.
Return JSON: {"hook": "..."}
Max 28 words. Mention company name."""


def _first_name(full_name: str) -> str:
    part = full_name.strip().split()[0] if full_name.strip() else "there"
    return part.capitalize() if len(part) >= 2 else "there"


def _company_key(company_name: str, domain: str | None) -> str | None:
    low = company_name.lower().strip()
    for key in KNOWN_COMPANY_HOOKS:
        if key in low:
            return key
    if domain:
        d = domain.lower().replace("www.", "")
        for key in KNOWN_COMPANY_HOOKS:
            if key in d:
                return key
    return None


def _clean_job_title(title: str, fallback_role: str | None) -> str:
    t = re.sub(r"\s+", " ", (title or "").strip())
    t = re.sub(
        r"^(in my role as|my role as|working as|as an?|as)\s+",
        "",
        t,
        flags=re.I,
    )
    if not t or len(t) < 3 or "in my role" in t.lower():
        return fallback_role or "your team"
    return t


def _clean_research_snippet(text: str) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    s = re.sub(r"\|.*$", "", s)
    return s.strip()


def _hook_from_research(company_name: str, raw: str) -> str:
    s = _clean_research_snippet(raw)
    if not s or len(s) < 25:
        return (
            f"{company_name}'s product and engineering direction stands out compared "
            "with most players in the space."
        )
    if len(s) > 160:
        s = re.split(r"(?<=[.!?])\s+", s)[0][:140]
    co = company_name.strip()
    low = s.lower()
    if co.lower() in low and (" is " in low or " are " in low):
        return s if s[-1] in ".!?" else s + "."
    theme = s
    if co.lower() in low:
        idx = low.find(co.lower())
        start = idx + len(co)
        theme = s[start:].strip(" -–—:,.")[:80] or "product and platform work"
    return (
        f"{co}'s work on {theme} is one of the more practical bets in the market right now."
    )


def _pick_experience_bullets(claims: list[str], max_items: int = 4) -> list[str]:
    if not claims:
        return [
            "Hands-on delivery of data and ML features in production environments.",
            "Cross-functional work with product and engineering stakeholders.",
        ]

    scored: list[tuple[int, str]] = []
    for c in claims:
        if not isinstance(c, str):
            continue
        line = re.sub(r"\s+", " ", c.strip())
        if len(line) < 20:
            continue
        if len(line) > 220:
            line = line[:217].rsplit(" ", 1)[0] + "..."
        score = 0
        low = line.lower()
        for kw in (
            "built",
            "developed",
            "led",
            "designed",
            "shipped",
            "implemented",
            "improved",
            "genai",
            "llm",
            "rag",
            "machine learning",
            "product",
            "python",
            "%",
            "users",
            "revenue",
        ):
            if kw in low:
                score += 1
        scored.append((score, line))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [line for _, line in scored[:max_items]]
    if not picked:
        picked = [claims[0].strip()[:200]]
    return picked


def _skills_summary(claims: list[str]) -> str:
    if not claims:
        return "applied ML, data engineering, and production delivery"

    blob = " ".join(claims).lower()
    tags: list[str] = []
    if re.search(r"product manager|\bpm\b", blob):
        tags.append("product management")
    if re.search(r"\b(genai|generative|llm)\b", blob):
        tags.append("GenAI/LLM")
    if re.search(r"\brag\b|retrieval", blob):
        tags.append("RAG")
    if re.search(r"machine learning|\bml\b", blob):
        tags.append("machine learning")
    if re.search(r"data engineer|data science", blob):
        tags.append("data engineering")
    if re.search(r"\bpython\b", blob):
        tags.append("Python")

    if tags:
        return ", ".join(list(dict.fromkeys(tags))[:5])
    return "end-to-end product and data work"


def _contribution_paragraph(
    company_name: str,
    company_key: str | None,
    target_role: str,
    claims: list[str],
) -> str:
    role_low = target_role.lower()
    if company_key:
        for (ck, role_hint), text in CONTRIBUTION_BY_ROLE.items():
            if ck == company_key and role_hint in role_low:
                return text

    skills = _skills_summary(claims)
    return (
        f"At {company_name}, I could contribute by bringing {skills} to problems your team "
        f"already cares about—partnering closely with engineering, product, and data so work "
        f"ships with measurable impact."
    )


def _compose_email(
    first: str,
    person_title: str,
    company_name: str,
    role: str,
    hook: str,
    bullets: list[str],
    contribution: str,
    skills_summary: str,
    sig: str,
) -> tuple[str, str]:
    title_clean = _clean_job_title(person_title, role)
    bullet_block = "\n".join(f"• {b}" for b in bullets)

    subject = f"{role} opportunity at {company_name} — background & fit"
    body = f"""Dear {first},

I hope you are doing well. I am reaching out about {role} opportunities at {company_name}. I have followed your company's direction for some time, and given your work as {title_clean}, I would value your guidance on how the team is hiring and where a candidate with my background could add value.

{hook.rstrip(".")}.

What I have worked on so far (from my own experience only):
{bullet_block}

Relevant strengths I would bring: {skills_summary}.

How I could contribute on your platform:
{contribution}

I would appreciate a brief call when convenient—or an introduction to the right hiring contact if someone else owns recruiting for this role.

Best regards,
{sig}"""
    return subject, body.strip()


def _compose_linkedin(
    first: str,
    hook: str,
    skills_summary: str,
    top_bullet: str | None,
    thanks_name: str,
) -> str:
    hook_line = hook.rstrip(".")
    extra = ""
    if top_bullet and len(top_bullet) < 90:
        short = top_bullet.rstrip(".")
        extra = f" Recently: {short}."

    msg = (
        f"Hi {first},\n"
        f"{hook_line}. I would love to contribute. "
        f"My background includes {skills_summary}.{extra}\n"
        f"Would you be open to a quick call?\n"
        f"Thanks,\n"
        f"{thanks_name}"
    )
    if len(msg) > 300:
        msg = (
            f"Hi {first},\n"
            f"{hook_line}. I would love to contribute. "
            f"Background: {skills_summary}.\n"
            f"Would you be open to a quick call?\n"
            f"Thanks,\n"
            f"{thanks_name}"
        )
    return msg.strip()


async def _resolve_hook(
    company_name: str,
    domain: str | None,
    raw_angle: str,
) -> str:
    key = _company_key(company_name, domain)
    if key:
        return KNOWN_COMPANY_HOOKS[key]

    hook = _hook_from_research(company_name, raw_angle)
    if os.getenv("OUTREACH_USE_LLM", "").lower() in ("1", "true", "yes"):
        try:
            raw = await llm_json_completion(
                HOOK_LLM_SYSTEM,
                {"companyName": company_name, "rawResearch": raw_angle},
            )
            polished = (raw.get("hook") or "").strip()
            if polished and len(polished.split()) <= 32:
                return polished if polished[-1] in ".!?" else polished + "."
        except ValueError:
            pass
    return hook


async def draft_cold_email(
    company_name: str,
    person_name: str,
    person_title: str,
    matched_role: str | None = None,
    resume_id: str | None = None,
    company_domain: str | None = None,
) -> dict:
    research = await research_company_angle(company_name, company_domain)
    ckey = _company_key(company_name, company_domain)
    hook = await _resolve_hook(
        company_name, company_domain, research.get("companyAngle", "")
    )

    role = matched_role or "this role"
    first = _first_name(person_name)
    candidate_name: str | None = None
    candidate_email: str | None = None
    claims: list[str] = []

    if resume_id:
        resume = load_resume(resume_id)
        if resume:
            facts = resume["parsedFacts"]
            contact = facts.get("contact") or {}
            candidate_name = contact.get("name")
            candidate_email = contact.get("email")
            raw_claims = facts.get("allowedClaims") or []
            claims = [c for c in raw_claims if isinstance(c, str)][:30]

    thanks = _first_name(candidate_name) if candidate_name else "Archit"
    signer = candidate_name or "[Your name]"
    sig = f"{signer}\n{candidate_email}" if candidate_email else signer

    bullets = _pick_experience_bullets(claims, 4)
    skills_summary = _skills_summary(claims)
    contribution = _contribution_paragraph(company_name, ckey, role, claims)

    subject, body = _compose_email(
        first,
        person_title,
        company_name,
        role,
        hook,
        bullets,
        contribution,
        skills_summary,
        sig,
    )
    top = bullets[0] if bullets else None
    linkedin = _compose_linkedin(first, hook, skills_summary, top, thanks)

    return {
        "subject": subject,
        "body": body,
        "linkedInMessage": linkedin,
        "companyAngle": hook,
        "recipientName": person_name,
        "companyName": company_name,
        "source": "structured",
    }
