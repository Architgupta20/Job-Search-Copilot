"""Fetch job posting text for ATS and tailoring."""

import re

from bs4 import BeautifulSoup

from app.services.company.jobs import fetch_html


async def fetch_job_posting_text(
    url: str,
    title: str,
    snippet: str | None = None,
) -> str:
    """Best-effort full posting text from job URL."""
    html = await fetch_html(url, timeout=22.0)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        main = (
            soup.find("div", class_=re.compile(r"content|description|posting", re.I))
            or soup.find("article")
            or soup.body
        )
        if main:
            text = main.get_text("\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            if len(text) >= 120:
                return f"{title}\n\n{text[:14000]}"

    parts = [title]
    if snippet:
        parts.append(snippet)
    return "\n\n".join(parts)


def job_text_for_ats_preview(job: dict) -> str:
    """Lightweight text from listing (no extra HTTP)."""
    parts = [
        job.get("title") or "",
        job.get("snippet") or "",
        job.get("location") or "",
        job.get("matchedRole") or "",
    ]
    return "\n".join(p for p in parts if p).strip()
