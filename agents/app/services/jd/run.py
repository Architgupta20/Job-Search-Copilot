import json
import re
import uuid
from io import BytesIO

from docx import Document

from app.config import JD_RUNS_DIR
from app.services.llm.client import rewrite_resume_bullets_llm
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


JD_PHRASE_PATTERNS = (
    r"\ba plus\b",
    r"\brequired\b",
    r"\bpreferred\b",
    r"\bmust have\b",
    r"\bwe are looking\b",
    r"\byou will\b",
    r"\bcandidates?\b",
    r"\bqualifications?\b",
    r"\ball about you\b",
    r"\bskills required\b",
    r"\bresponsibilities\b",
    r"\bwhat you.ll\b",
)


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


def _is_valid_resume_bullet(line: str) -> bool:
    if len(line) < 25:
        return False
    if line.isupper() and len(line) < 90:
        return False
    if re.match(r"^[\w\s/&+-]+:$", line):
        return False
    return True


def _line_in_resume(line: str, resume_text: str) -> bool:
    line_l = _norm(line).lower()
    resume_l = resume_text.lower()
    if line_l in resume_l:
        return True
    line_tokens = _tokens(line)
    if not line_tokens:
        return False
    for raw in resume_text.splitlines():
        chunk = _norm(raw)
        if len(chunk) < 20:
            continue
        overlap = len(line_tokens & _tokens(chunk))
        if overlap / max(len(line_tokens), 1) >= 0.88:
            return True
    return False


def _looks_like_jd_requirement(line: str, jd_text: str, resume_text: str) -> bool:
    line_l = _norm(line).lower()
    if not _line_in_resume(line, resume_text):
        return True
    jd_l = jd_text.lower()
    if len(line_l) > 35 and line_l in jd_l:
        # Long sentence copied from posting — only allow if clearly present in resume upload.
        if line_l not in resume_text.lower():
            return True
    for pat in JD_PHRASE_PATTERNS:
        if re.search(pat, line_l):
            return True
    return False


def _extract_resume_bullets(
    raw_text: str, allowed_claims: list[str]
) -> list[tuple[str, str]]:
    """Return (section, bullet_text) only from the uploaded resume."""
    sections = _extract_resume_sections(raw_text)
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    def add(section: str, text: str) -> None:
        t = _norm(text)
        key = t.lower()
        if not _is_valid_resume_bullet(t) or key in seen:
            return
        seen.add(key)
        out.append((section, t))

    for section_name, lines in sections:
        for line in lines:
            add(section_name, line)

    for claim in allowed_claims:
        t = _norm(claim)
        if not t:
            continue
        section = _section_for_line(t, sections)
        add(section, t)

    return out


def _jd_keywords_in_bullet(bullet: str, jd_keywords: list[str]) -> list[str]:
    blob = bullet.lower()
    return [kw for kw in jd_keywords if kw in blob]


def _guess_jd_title(jd_text: str) -> str | None:
    for line in jd_text.splitlines()[:8]:
        t = _norm(line)
        if 8 < len(t) < 90 and re.search(
            r"engineer|analyst|manager|scientist|developer|designer|lead|architect",
            t,
            re.I,
        ):
            return t
    first = _norm(jd_text.splitlines()[0]) if jd_text.splitlines() else ""
    return first[:90] if first else None


def _simple_rewrite(bullet: str, keywords: list[str]) -> str:
    """Fallback when LLM rewrite missing — light keyword emphasis only."""
    if not keywords:
        return bullet
    missing = [kw for kw in keywords if kw.lower() not in bullet.lower()]
    if not missing:
        return bullet
    tail = ", ".join(missing[:3])
    return f"{bullet.rstrip('.')} — emphasizing {tail}."


def _apply_edits_to_resume(raw_text: str, edits: list[dict]) -> str:
    updated = raw_text
    for e in edits:
        orig = e.get("original") or ""
        sugg = e.get("suggested") or ""
        if orig and sugg and orig in updated:
            updated = updated.replace(orig, sugg, 1)
    return normalize_line_breaks(updated)


async def _build_edits_from_resume(
    *,
    raw_text: str,
    allowed_claims: list[str],
    jd_text: str,
    jd_keywords: list[str],
    max_edits: int = 6,
) -> list[dict]:
    bullets = _extract_resume_bullets(raw_text, allowed_claims)
    selected: list[tuple[int, str, str, list[str]]] = []

    for section, text in bullets:
        if _looks_like_jd_requirement(text, jd_text, raw_text):
            continue
        hits = _jd_keywords_in_bullet(text, jd_keywords)
        if not hits:
            continue
        selected.append((len(hits), section, text, hits))

    selected.sort(key=lambda x: x[0], reverse=True)
    selected = selected[:max_edits]

    if not selected:
        return []

    llm_payload = [
        {
            "id": i + 1,
            "section": section,
            "original": text,
            "keywordsToWeave": hits[:8],
        }
        for i, (_, section, text, hits) in enumerate(selected)
    ]
    rewrites = await rewrite_resume_bullets_llm(llm_payload)

    edits: list[dict] = []
    for i, (_, section, text, hits) in enumerate(selected):
        rid = i + 1
        suggested = rewrites.get(rid) or _simple_rewrite(text, hits)
        edits.append(
            {
                "section": section,
                "original": text,
                "suggested": _norm(suggested),
                "reason": (
                    f"Resume bullet matched JD keywords: {', '.join(hits[:6])}. "
                    "Rewrite keeps your facts; only wording is adjusted."
                ),
            }
        )
    return edits


async def run_jd_tailor(resume_id: str, jd_text: str) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found.")

    facts = resume["parsedFacts"]
    raw_text = facts["rawText"]
    claims = facts["allowedClaims"]
    jd_keywords = extract_jd_keywords(jd_text)

    suggested_edits = await _build_edits_from_resume(
        raw_text=raw_text,
        allowed_claims=claims,
        jd_text=jd_text,
        jd_keywords=jd_keywords,
    )

    if suggested_edits:
        text = _apply_edits_to_resume(raw_text, suggested_edits)
    else:
        text = normalize_line_breaks(raw_text)

    keywords_used: list[str] = []
    for e in suggested_edits:
        for kw in _jd_keywords_in_bullet(e["original"], jd_keywords):
            if kw not in keywords_used:
                keywords_used.append(kw)

    resume_blob = " ".join(claims).lower()
    skipped = [
        kw for kw in jd_keywords if kw not in resume_blob and kw not in keywords_used
    ]
    ats = compute_ats_breakdown(jd_keywords, claims, keywords_used)

    warnings = [
        "Edits are built only from bullets/lines in your uploaded resume that match JD keywords — not from JD requirement text.",
        "Copy each green rewrite into your Word file at the section shown.",
    ]
    if not suggested_edits:
        warnings.append(
            "No resume bullets matched this JD yet. Try a role closer to your experience, or upload a resume with clearer bullet points."
        )
    if skipped:
        warnings.append(
            f"{len(skipped)} JD keyword(s) are not in your resume and were not invented."
        )

    change_summary = [
        f"{e['section']}: updated bullet for {', '.join(_jd_keywords_in_bullet(e['original'], jd_keywords)[:4])}"
        for e in suggested_edits
    ]

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "jdTitle": _guess_jd_title(jd_text),
        "tailoredText": text,
        "suggestedEdits": suggested_edits,
        "keywordsUsed": keywords_used,
        "keywordsSkipped": skipped,
        "atsScorePercent": ats["scorePercent"],
        "atsBreakdown": ats,
        "changeSummary": change_summary,
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
