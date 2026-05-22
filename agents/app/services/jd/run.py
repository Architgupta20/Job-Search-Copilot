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

    text = normalize_line_breaks(tailored.get("tailoredText", "").strip())
    if not text and not tailored.get("suggestedEdits"):
        raise ValueError("Tailoring produced no content.")

    keywords_used = tailored.get("keywordsUsed") or []
    skipped = tailored.get("keywordsSkipped") or []
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
        "suggestedEdits": tailored.get("suggestedEdits") or [],
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
