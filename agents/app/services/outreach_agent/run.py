"""Outreach agent — next-best actions and drafts from tracker + resume."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from app.config import RUNS_DIR
from app.services.company.cold_email import (
    _first_name,
    _pick_experience_bullets,
    draft_cold_email,
)
from app.services.resume.parser import load_resume

FOLLOW_UP_AFTER_DAYS = 5
WAIT_MIN_DAYS = 2

ACTION_LABELS: dict[str, str] = {
    "initial_outreach": "Send initial outreach",
    "follow_up": "Send follow-up",
    "thank_reply": "Reply and schedule next step",
    "interview_prep": "Prepare for interview",
    "wait": "Wait before following up",
    "none": "No outreach action",
}


def _parse_iso(iso: str | None) -> datetime | None:
    if not iso or not str(iso).strip():
        return None
    try:
        raw = str(iso).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _days_since(iso: str | None) -> int:
    dt = _parse_iso(iso)
    if not dt:
        return 0
    now = datetime.now(timezone.utc)
    return max(0, int((now - dt).total_seconds() // 86400))


def _recommend(
    *,
    status: str,
    outreach_sent_at: str | None,
    contact_name: str | None,
) -> tuple[str, str, str]:
    """Returns (action, priority, reason)."""
    days = _days_since(outreach_sent_at)
    has_contact = bool((contact_name or "").strip())

    if status in ("rejected", "offer"):
        return (
            "none",
            "low",
            "Terminal status — no outreach recommended.",
        )

    if status == "interview":
        return (
            "interview_prep",
            "high",
            "Interview stage — review STAR stories tied to your resume.",
        )

    if status == "replied":
        return (
            "thank_reply",
            "high",
            "They replied — send a short note to confirm interest and propose times.",
        )

    if status in ("saved", "applied"):
        if not outreach_sent_at:
            if has_contact:
                return (
                    "initial_outreach",
                    "high",
                    "No outreach logged yet — draft a resume-backed cold email.",
                )
            return (
                "initial_outreach",
                "medium",
                "Add a contact name on the tracker row, then send initial outreach.",
            )

        if days >= FOLLOW_UP_AFTER_DAYS:
            return (
                "follow_up",
                "high",
                f"No reply in {days} days — send a polite follow-up.",
            )
        if days >= WAIT_MIN_DAYS:
            remaining = FOLLOW_UP_AFTER_DAYS - days
            return (
                "wait",
                "low",
                f"Give them {remaining} more day(s) before following up (sent {days}d ago).",
            )
        return (
            "wait",
            "low",
            f"Outreach sent {days} day(s) ago — wait until day {FOLLOW_UP_AFTER_DAYS} for follow-up.",
        )

    return ("none", "low", "No action for this status.")


def _interview_prep_path(company: str, role: str) -> str:
    return (
        f"/interview-prep?company={quote(company)}&role={quote(role)}"
    )


async def _draft_follow_up(
    *,
    company_name: str,
    role_title: str,
    person_name: str,
    claims: list[str],
    days_since: int,
) -> dict[str, str]:
    first = _first_name(person_name)
    company = company_name.strip()
    role = role_title.strip()
    bullets = _pick_experience_bullets(claims, 2)
    reminder = ""
    if bullets:
        reminder = (
            f"\n\nAs a quick reminder, my background includes work such as: {bullets[0].rstrip('.')}."
        )

    subject = f"Following up — {role} at {company}"
    body = f"""Hi {first},

I hope you are doing well. I wanted to follow up on my note regarding the {role} opportunity at {company}.

I remain very interested in the role and would welcome a brief conversation if you have time.{reminder}

Thank you again for your consideration.

Best regards"""

    linkedin = (
        f"Hi {first} — following up on the {role} role at {company}. "
        f"Still very interested; happy to connect briefly if convenient. Thank you."
    )

    return {
        "subject": subject,
        "body": body.strip(),
        "linkedInMessage": linkedin,
        "kind": "follow_up",
        "daysSinceOutreach": days_since,
    }


def _draft_thank_reply(
    *,
    company_name: str,
    role_title: str,
    person_name: str,
) -> dict[str, str]:
    first = _first_name(person_name)
    company = company_name.strip()
    role = role_title.strip()
    subject = f"Re: {role} at {company}"
    body = f"""Hi {first},

Thank you for getting back to me about the {role} role at {company}. I appreciate your time.

I remain very interested and would be glad to share more detail on my background or join a call at a time that works for you. Please let me know what works best on your side.

Best regards"""

    linkedin = (
        f"Hi {first} — thanks for your reply on the {role} role at {company}. "
        "Happy to jump on a quick call whenever works for you."
    )

    return {
        "subject": subject,
        "body": body.strip(),
        "linkedInMessage": linkedin,
        "kind": "thank_reply",
    }


async def _build_draft_for_action(
    action: str,
    *,
    company_name: str,
    role_title: str,
    person_name: str,
    person_title: str,
    resume_id: str | None,
    outreach_sent_at: str | None,
    claims: list[str],
) -> dict[str, Any] | None:
    if action == "initial_outreach":
        return await draft_cold_email(
            company_name,
            person_name,
            person_title,
            matched_role=role_title,
            resume_id=resume_id,
        )
    if action == "follow_up":
        return await _draft_follow_up(
            company_name=company_name,
            role_title=role_title,
            person_name=person_name,
            claims=claims,
            days_since=_days_since(outreach_sent_at),
        )
    if action == "thank_reply":
        return _draft_thank_reply(
            company_name=company_name,
            role_title=role_title,
            person_name=person_name,
        )
    return None


async def run_outreach_agent(
    resume_id: str,
    applications: list[dict[str, Any]],
) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found. Upload again from home.")

    facts = resume["parsedFacts"]
    contact = facts.get("contact") or {}
    default_signer = contact.get("name") or "there"
    claims = [c for c in (facts.get("allowedClaims") or []) if isinstance(c, str)]

    plans: list[dict[str, Any]] = []
    priority_order = {"high": 0, "medium": 1, "low": 2}

    for app in applications:
        app_id = str(app.get("id") or "")
        company = str(app.get("company") or "").strip()
        role = str(app.get("role") or "").strip()
        status = str(app.get("status") or "saved").strip()
        contact_name = (app.get("contactName") or "").strip() or "Hiring Manager"
        person_title = (app.get("contactTitle") or role).strip()
        outreach_sent_at = app.get("outreachSentAt")

        action, priority, reason = _recommend(
            status=status,
            outreach_sent_at=outreach_sent_at,
            contact_name=contact_name if contact_name != "Hiring Manager" else None,
        )

        draft: dict[str, Any] | None = None
        if action in ("initial_outreach", "follow_up", "thank_reply"):
            try:
                draft = await _build_draft_for_action(
                    action,
                    company_name=company,
                    role_title=role,
                    person_name=contact_name,
                    person_title=person_title,
                    resume_id=resume_id,
                    outreach_sent_at=outreach_sent_at,
                    claims=claims,
                )
            except Exception:
                draft = None

        links: dict[str, str] = {}
        if action == "interview_prep":
            links["interviewPrep"] = _interview_prep_path(company, role)

        plans.append(
            {
                "applicationId": app_id,
                "companyName": company,
                "roleTitle": role,
                "status": status,
                "recommendedAction": action,
                "actionLabel": ACTION_LABELS.get(action, action),
                "priority": priority,
                "reason": reason,
                "draft": draft,
                "links": links,
            }
        )

    plans.sort(
        key=lambda p: (
            priority_order.get(p.get("priority", "low"), 9),
            p.get("companyName", ""),
        )
    )

    high = sum(1 for p in plans if p.get("priority") == "high" and p.get("recommendedAction") != "none")
    by_action: dict[str, int] = {}
    for p in plans:
        a = p.get("recommendedAction") or "none"
        by_action[a] = by_action.get(a, 0) + 1

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "candidateName": default_signer,
        "plans": plans,
        "summary": {
            "total": len(plans),
            "highPriority": high,
            "byAction": by_action,
        },
        "warnings": [
            "Plans use resume-backed drafts where possible — edit before sending.",
            f"Follow-up timing: {FOLLOW_UP_AFTER_DAYS}+ days after logging outreach sent.",
        ],
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"outreach-agent-{run_id}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result
