import re
import uuid
from io import BytesIO
from pathlib import Path

import fitz  # pymupdf
from docx import Document

from app.config import RESUMES_DIR

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


def extract_text(file_bytes: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    if lower.endswith(".pdf"):
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            return "\n".join(page.get_text() for page in pdf).strip()
    raise ValueError("Unsupported file type. Use PDF or DOCX.")


def build_allowed_claims(raw_text: str) -> list[str]:
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in raw_text.splitlines()
        if len(line.strip()) >= 12
    ]
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out[:200]


def build_parsed_facts(raw_text: str) -> dict:
    lines = [l.strip() for l in raw_text.splitlines()]
    top = " ".join(lines[:8])
    email = EMAIL_RE.search(top) or EMAIL_RE.search(raw_text)
    phone = PHONE_RE.search(top) or PHONE_RE.search(raw_text)
    name = None
    for line in lines[:8]:
        if (
            2 < len(line) < 60
            and not EMAIL_RE.search(line)
            and not PHONE_RE.search(line)
            and not re.match(r"^(experience|education|skills|summary)", line, re.I)
        ):
            name = line
            break
    return {
        "contact": {
            "name": name,
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None,
        },
        "rawText": raw_text,
        "allowedClaims": build_allowed_claims(raw_text),
    }


def save_resume(file_bytes: bytes, filename: str, mime_type: str, parsed_facts: dict) -> dict:
    resume_id = str(uuid.uuid4())
    folder = RESUMES_DIR / resume_id
    folder.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".bin"
    stored = folder / f"original{ext}"
    stored.write_bytes(file_bytes)
    record = {
        "id": resume_id,
        "fileName": filename,
        "mimeType": mime_type,
        "storedPath": str(stored),
        "uploadedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "parsedFacts": parsed_facts,
    }
    import json

    (folder / "meta.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def load_resume(resume_id: str) -> dict | None:
    import json

    meta = RESUMES_DIR / resume_id / "meta.json"
    if not meta.exists():
        return None
    return json.loads(meta.read_text(encoding="utf-8"))
