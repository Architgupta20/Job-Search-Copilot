from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.company.cold_email import draft_cold_email
from app.services.company.run import run_company_search, tailor_resume_for_job
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/company", tags=["company"])


class CompanyRunBody(BaseModel):
    resumeId: str | None = None
    companyName: str
    targetRoles: list[str] = Field(min_length=1)
    careersUrlOverride: str | None = None


@router.post("/run")
async def company_run(body: CompanyRunBody):
    if not body.companyName.strip():
        raise HTTPException(400, "companyName is required.")
    if not body.targetRoles:
        raise HTTPException(400, "Select at least one target role.")

    if body.resumeId and not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")

    try:
        override = (body.careersUrlOverride or "").strip() or None
        return await run_company_search(
            body.companyName.strip(),
            body.targetRoles,
            resume_id=body.resumeId,
            careers_url_override=override,
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e


class JobTailorBody(BaseModel):
    resumeId: str
    jobUrl: str
    jobTitle: str
    snippet: str | None = None
    confirmed: bool = True


@router.post("/job/tailor")
async def tailor_job(body: JobTailorBody):
    if not body.confirmed:
        raise HTTPException(400, "Confirm your resume is accurate.")
    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload on home first.")
    try:
        return await tailor_resume_for_job(
            body.resumeId,
            body.jobUrl,
            body.jobTitle,
            body.snippet,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


class ColdEmailBody(BaseModel):
    companyName: str
    personName: str
    personTitle: str
    matchedRole: str | None = None
    resumeId: str | None = None
    companyDomain: str | None = None


@router.post("/cold-email")
async def cold_email(body: ColdEmailBody):
    if not body.companyName.strip() or not body.personName.strip():
        raise HTTPException(400, "companyName and personName are required.")
    if body.resumeId and not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")
    try:
        return await draft_cold_email(
            body.companyName.strip(),
            body.personName.strip(),
            body.personTitle.strip(),
            body.matchedRole,
            resume_id=body.resumeId,
            company_domain=body.companyDomain,
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e
