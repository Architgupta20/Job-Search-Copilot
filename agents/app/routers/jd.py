from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel

from app.services.jd.run import build_docx_bytes, load_jd_run, run_jd_tailor
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/jd", tags=["jd"])


class JdRunBody(BaseModel):
    resumeId: str
    jdText: str
    confirmed: bool = False


@router.post("/run")
async def jd_run(body: JdRunBody):
    if not body.confirmed:
        raise HTTPException(400, "Please confirm your resume information is accurate.")
    if not body.jdText.strip() or len(body.jdText.strip()) < 80:
        raise HTTPException(400, "Paste a job description (at least 80 characters).")

    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")

    try:
        return await run_jd_tailor(body.resumeId, body.jdText.strip())
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/{run_id}/download")
async def jd_download(
    run_id: str,
    file_format: str = Query("docx", alias="format"),
):
    result = load_jd_run(run_id)
    if not result:
        raise HTTPException(404, "Run not found.")

    resume = load_resume(result["resumeId"])
    if not resume:
        raise HTTPException(404, "Original resume not found.")

    if file_format == "txt":
        filename = f"tailored-resume-{run_id[:8]}.txt"
        return PlainTextResponse(
            result["tailoredText"],
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    is_docx = resume["mimeType"].endswith("wordprocessingml") or resume[
        "fileName"
    ].lower().endswith(".docx")
    blob = build_docx_bytes(
        result["tailoredText"],
        resume.get("storedPath"),
        is_docx,
    )
    base = resume["fileName"].rsplit(".", 1)[0] or "resume"
    filename = f"{base}-tailored.docx"
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Template-Preserved": "1" if is_docx else "0",
        },
    )
