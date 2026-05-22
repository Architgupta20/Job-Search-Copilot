"""Draft cold outreach: full email + LinkedIn message."""

from app.services.llm.client import llm_json_completion
from app.services.resume.parser import load_resume

COLD_OUTREACH_SYSTEM = """You write professional job-seeker outreach for ONE recipient.

Return JSON only:
{
  "subject": "clear email subject line",
  "body": "complete business email in plain text",
  "linkedInMessage": "short LinkedIn connection or InMail note"
}

EMAIL body rules (must look like a real email, NOT a chat message):
- Start with "Dear {FirstName}," (use recipient first name)
- 2–3 short paragraphs (3–5 sentences total across paragraphs)
- Paragraph 1: why you are reaching out (their role + company + your interest in the target role)
- Paragraph 2: ONE or TWO real highlights from allowedClaims only if provided — never invent employers, degrees, tools, or metrics
- Paragraph 3: polite ask (brief call or referral) and thanks
- End with "Best regards," then blank line then candidate full name; if candidateEmail in payload add it on next line
- Total body roughly 120–220 words
- No markdown, no bullet lists

LinkedIn message rules:
- Under 280 characters
- No "Dear", no subject line
- First line: hook about their role/company
- One sentence on you + ask to connect
- Warm, professional, not salesy"""


def _first_name(full_name: str) -> str:
    part = full_name.strip().split()[0] if full_name.strip() else "there"
    return part if len(part) >= 2 else "there"


def _template_outreach(
    company_name: str,
    person_name: str,
    person_title: str,
    matched_role: str | None,
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    claim_hint: str | None = None,
) -> dict:
    role = matched_role or "a relevant role"
    first = _first_name(person_name)
    signer = candidate_name or "[Your name]"
    sig = signer
    if candidate_email:
        sig = f"{signer}\n{candidate_email}"

    claim_para = ""
    if claim_hint:
        claim_para = (
            f"\n\nMy background includes experience aligned with your team — "
            f"for example, {claim_hint[:140].rstrip('.')}. "
            "I believe this could be relevant to the work you lead."
        )

    subject = f"Inquiry regarding {role} opportunities at {company_name}"
    body = f"""Dear {first},

I hope this email finds you well. I am reaching out because of your position as {person_title} at {company_name}. I am actively exploring {role} opportunities on your team and wanted to introduce myself professionally.{claim_para}

Would you be open to a brief conversation, or could you kindly point me to the right person for hiring in this area? I would greatly appreciate your time and guidance.

Best regards,
{sig}"""

    linkedin = (
        f"Hi {first} — I admire the work your team is doing at {company_name} as {person_title}. "
        f"I'm exploring {role} roles and would value connecting. Thank you!"
    )[:280]

    return {
        "subject": subject,
        "body": body.strip(),
        "linkedInMessage": linkedin,
        "recipientName": person_name,
        "companyName": company_name,
        "source": "template",
    }


async def draft_cold_email(
    company_name: str,
    person_name: str,
    person_title: str,
    matched_role: str | None = None,
    resume_id: str | None = None,
) -> dict:
    payload: dict = {
        "companyName": company_name,
        "recipientName": person_name,
        "recipientFirstName": _first_name(person_name),
        "recipientTitle": person_title,
        "targetRole": matched_role or "relevant roles",
    }

    candidate_name: str | None = None
    candidate_email: str | None = None
    claim_hint: str | None = None

    if resume_id:
        resume = load_resume(resume_id)
        if resume:
            facts = resume["parsedFacts"]
            contact = facts.get("contact") or {}
            candidate_name = contact.get("name")
            candidate_email = contact.get("email")
            claims = facts.get("allowedClaims") or []
            payload["candidateName"] = candidate_name
            payload["candidateEmail"] = candidate_email
            payload["allowedClaims"] = claims[:20]
            if claims:
                claim_hint = claims[0]

    try:
        raw = await llm_json_completion(COLD_OUTREACH_SYSTEM, payload)
        body = (raw.get("body") or "").strip()
        if body and not body.lower().startswith("dear"):
            body = f"Dear {_first_name(person_name)},\n\n{body}"
        if body and "best regards" not in body.lower():
            sig = candidate_name or "[Your name]"
            if candidate_email:
                sig = f"{sig}\n{candidate_email}"
            body = f"{body.rstrip()}\n\nBest regards,\n{sig}"

        linkedin = (raw.get("linkedInMessage") or "").strip()
        if len(linkedin) > 300:
            linkedin = linkedin[:297] + "..."

        return {
            "subject": (raw.get("subject") or "Professional introduction").strip(),
            "body": body,
            "linkedInMessage": linkedin or _template_outreach(
                company_name,
                person_name,
                person_title,
                matched_role,
                candidate_name,
                candidate_email,
                claim_hint,
            )["linkedInMessage"],
            "recipientName": person_name,
            "companyName": company_name,
            "source": "llm",
        }
    except ValueError as e:
        msg = str(e)
        out = _template_outreach(
            company_name,
            person_name,
            person_title,
            matched_role,
            candidate_name,
            candidate_email,
            claim_hint,
        )
        if "restricted" in msg.lower() or "401" in msg:
            out["warning"] = (
                "Groq blocked this request. Using template drafts — fix apps/web/.env "
                "(new Groq key, ollama, or openai) and restart uvicorn."
            )
        else:
            out["warning"] = f"LLM unavailable — using template drafts. ({msg[:160]})"
        return out
