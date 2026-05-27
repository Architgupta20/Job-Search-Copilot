import json
import re
import uuid
from io import BytesIO

from docx import Document

from app.config import JD_RUNS_DIR
from app.services.llm.client import tailor_resume_llm
from app.services.resume.parser import load_resume

SECTION_HEADERS = [
    "WORK EXPERIENCE", "EDUCATION", "PROJECTS", "SKILLS", "SUMMARY", "EXPERIENCE",
]

CANONICAL_SECTIONS = {
    "work experience": "Work Experience",
    "experience": "Work Experience",
    "professional experience": "Work Experience",
    "employment": "Work Experience",
    "education": "Education",
    "projects": "Projects",
    "skills": "Skills",
    "summary": "Summary",
    "certifications": "Certifications",
    "achievements": "Achievements",
}


def normalize_line_breaks(text: str) -> str:
    result = text.replace("\r\n", "\n").strip()
    if "\n\n" not in result:
        for h in SECTION_HEADERS:
            result = re.sub(rf"\s+({h}:?)", r"\n\n\1\n", result, flags=re.I)
    result = re.sub(r"([.!?])\s+(-\s+)", r"\1\n\2", result)
    return re.sub(r"\n{3,}", "\n\n", result)


def extract_jd_keywords(jd_text: str) -> list[str]:
    words = re.findall(r"[a-z0-9+.#-]{3,}", jd_text.lower())
    stop = {
        "the", "and", "for", "with", "you", "will", "our", "are", "this", "that",
        "role", "about", "what", "your", "have", "from", "into", "that", "this",
    }
    freq: dict[str, int] = {}
    for w in words:
        if w not in stop and len(w) >= 3:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:40]]


def compute_ats_breakdown(
    jd_keywords: list[str],
    claims: list[str],
    used: list[str],
) -> dict:
    blob = " ".join(claims).lower()
    used_blob = " ".join(used).lower()
    matched: list[str] = []
    missing: list[str] = []
    for kw in jd_keywords:
        if kw in blob or kw in used_blob or any(kw in u.lower() for u in used):
            matched.append(kw)
        else:
            missing.append(kw)
    total = len(jd_keywords) or 1
    score = round(len(matched) / total * 100)
    return {
        "scorePercent": score,
        "totalKeywords": len(jd_keywords),
        "matchedKeywords": matched,
        "missingKeywords": missing,
        "supportedCount": len(matched),
    }


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.-]{3,}", (s or "").lower()))


def _canonical_section_name(section: str | None) -> str:
    key = _norm(section or "").lower().rstrip(":")
    if key in CANONICAL_SECTIONS:
        return CANONICAL_SECTIONS[key]
    return _norm(section or "") or "General"


def _extract_resume_sections(raw_text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_name = "General"
    current_lines: list[str] = []

    for raw in raw_text.splitlines():
        line = _norm(raw)
        if not line:
            continue
        low = line.lower().rstrip(":")
        if low in CANONICAL_SECTIONS:
            if current_lines:
                sections.append((current_name, current_lines))
            current_name = CANONICAL_SECTIONS[low]
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_name, current_lines))
    return sections


def _best_resume_line(excerpt: str, claims: list[str]) -> str:
    needle = _norm(excerpt)
    if not needle:
        return ""
    needle_low = needle.lower()

    # Exact-ish containment first.
    for c in claims:
        cc = _norm(c)
        c_low = cc.lower()
        if needle_low and (needle_low in c_low or c_low in needle_low):
            return cc

    # Fallback to token overlap.
    needle_tokens = _tokens(needle)
    best = ""
    best_score = 0.0
    for c in claims:
        cc = _norm(c)
        c_tokens = _tokens(cc)
        if not c_tokens:
            continue
        overlap = len(needle_tokens & c_tokens)
        if overlap == 0:
            continue
        score = overlap / max(len(needle_tokens), 1)
        if score > best_score:
            best_score = score
            best = cc
    return best


def _section_for_line(line: str, sections: list[tuple[str, list[str]]]) -> str:
    line_low = _norm(line).lower()
    if not line_low:
        return "General"
    for section_name, lines in sections:
        for entry in lines:
            entry_low = _norm(entry).lower()
            if line_low in entry_low or entry_low in line_low:
                return section_name
    return "General"


def _normalize_suggested_edits(
    edits: list[dict] | None,
    *,
    raw_text: str,
    allowed_claims: list[str],
) -> list[dict]:
    sections = _extract_resume_sections(raw_text)
    claims = [_norm(c) for c in allowed_claims if _norm(c)]
    out: list[dict] = []

    for e in edits or []:
        if not isinstance(e, dict):
            continue
        original = _norm(str(e.get("original") or ""))
        suggested = _norm(str(e.get("suggested") or ""))
        reason = _norm(str(e.get("reason") or ""))
        section = _canonical_section_name(e.get("section"))
        if not original and not suggested:
            continue

        # Anchor "original" to an actual resume line if LLM returned vague text.
        anchored_original = _best_resume_line(original, claims) if original else ""
        if anchored_original:
            original = anchored_original
        elif claims:
            # Last resort: keep first claim so user always has a real edit anchor.
            original = claims[0]

        # Prefer section inferred from anchored resume line.
        inferred = _section_for_line(original, sections)
        if inferred != "General":
            section = inferred
        if not section:
            section = "General"

        out.append(
            {
                "section": section,
                "original": original,
                "suggested": suggested,
                "reason": reason or "Aligns with JD keywords supported by your resume.",
            }
        )
    return out


async def run_jd_tailor(resume_id: str, jd_text: str) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found.")

    facts = resume["parsedFacts"]
    jd_keywords = extract_jd_keywords(jd_text)
    tailored = await tailor_resume_llm({
        "jobDescription": jd_text[:8000],
        "jdKeywords": jd_keywords,
        "allowedClaims": facts["allowedClaims"][:120],
        "originalResume": facts["rawText"][:12000],
    })

    raw_tailored = (tailored.get("tailoredText") or "").strip()

    # Detect if the LLM returned JD requirements instead of the resume (common failure mode).
    # The resume's raw text should share significant tokens with the output.
    resume_tokens = set(re.findall(r"[a-z0-9]{4,}", facts["rawText"].lower()))
    output_tokens = set(re.findall(r"[a-z0-9]{4,}", raw_tailored.lower()))
    overlap = len(resume_tokens & output_tokens)
    resume_token_count = max(len(resume_tokens), 1)
    if raw_tailored and overlap / resume_token_count < 0.15:
        # Output shares less than 15% of resume vocabulary — likely returned JD text.
        # Fall back to the raw resume text as the draft so the user at least sees their resume.
        raw_tailored = facts["rawText"]

    text = normalize_line_breaks(raw_tailored)
    if not text and not tailored.get("suggestedEdits"):
        raise ValueError("Tailoring produced no content.")

    keywords_used = tailored.get("keywordsUsed") or []
    skipped = tailored.get("keywordsSkipped") or []
    normalized_edits = _normalize_suggested_edits(
        tailored.get("suggestedEdits") or [],
        raw_text=facts["rawText"],
        allowed_claims=facts["allowedClaims"],
    )
    ats = compute_ats_breakdown(jd_keywords, facts["allowedClaims"], keywords_used)

    warnings = [
        "Copy suggestions into your own Word file — download is plain text/DOCX, not your original layout."
    ]
    if skipped:
        warnings.append(
            f"{len(skipped)} JD keyword(s) not added (not supported by your resume)."
        )

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "jdTitle": tailored.get("jdTitle"),
        "tailoredText": text,
        "suggestedEdits": normalized_edits,
        "keywordsUsed": keywords_used,
        "keywordsSkipped": skipped,
        "atsScorePercent": ats["scorePercent"],
        "atsBreakdown": ats,
        "changeSummary": tailored.get("changeSummary") or [],
        "warnings": warnings,
    }
    JD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (JD_RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def build_docx_bytes(tailored_text: str, _original_path: str | None = None, _is_docx: bool = False) -> bytes:
    """Plain DOCX export only — never merge into user's uploaded template."""
    doc = Document()
    for line in tailored_text.splitlines():
        p = doc.add_paragraph(line.strip() or "")
        if line.strip().isupper() and len(line.strip()) < 50:
            for run in p.runs:
                run.bold = True
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def load_jd_run(run_id: str) -> dict | None:
    p = JD_RUNS_DIR / f"{run_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
